# pylint: disable=too-many-instance-attributes
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc import aio
from pytest import FixtureRequest


class CassetteManager:
    def __init__(self, request: FixtureRequest):
        self.request = request
        self.markers = list(request.node.iter_markers('allow_grpc'))

        self.generated = False
        self._iter = None

        self.allow_grpc = bool(self.markers)
        self.cassette_file = (
            Path(request.getfixturevalue('vcr_cassette_dir')) /
            request.getfixturevalue('default_cassette_name')
        ).with_suffix('.gprc.json')

        self.generate = request.config.getoption("--generate-grpc")
        self.regenerate = request.config.getoption("--regenerate-grpc")
        self.mode = 'write' if self.generate or self.regenerate else 'read'

    def assert_for_grpc(self):
        """
        Small precaution for users actually knows what they doing.

        NB: it will not work with stream_unary and stream_stream yet.
        """
        if not self.allow_grpc:
            raise RuntimeError('gprc requests is disabled, use @pytest.mark.allow_grpc on test')

    def new_cassette(self):
        assert self.mode == 'write'

        if self.regenerate:
            assert self.cassette_file.exists()

        if self.generate:
            assert not self.cassette_file.exists()

        data = {
            'interactions': []
        }
        self.cassette_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cassette_file.open('w') as f_:
            json.dump(data, f_)

    def read_cassette(self):
        with self.cassette_file.open('r', encoding='utf-8') as f_:
            return json.load(f_)

    def dump_proto_object(self, obj):
        return {
            'cls': type(obj).__name__,
            'module': type(obj).__module__,
            'message': MessageToDict(obj)
        }

    def read_proto_object(self, dct):
        module = importlib.import_module(dct['module'])
        cls = getattr(module, dct['cls'])
        message = cls()
        ParseDict(dct['message'], message)
        return message

    def write(self, request, response):
        """
        Write a new request to a cassette.

        At first call it will create a new file (or rewrite old one).
        We are obliged to read/write cassette file every time, because
        we don't know in advance when there will be a last write.
        """
        assert self.mode == 'write'
        if not self.generated:
            self.generated = True
            self.new_cassette()

        cassette = self.read_cassette()
        data = {
            'request': self.dump_proto_object(request)
        }
        cassette['interactions'].append(data)

        if isinstance(response, list):
            data['response_stream'] = [self.dump_proto_object(r) for r in response]
        else:
            data['response'] = self.dump_proto_object(response)

        with self.cassette_file.open('w') as f_:
            json.dump(cassette, f_, indent=4)

    def read_next(self, response_type, incoming_request):
        """
        Read next request from a cassette.

        It is highly depends on grpc call order and could break in case
        of some parallelism logic.

        Also, right now it is ignoring "request" field from a cassette,
        but in future we could compare it with incoming request for a greater
        deterministic of testing process.
        """
        assert incoming_request
        assert self.mode == 'read'
        if not self._iter:
            cassette = self.read_cassette()
            data = cassette['interactions']
            self._iter = iter(data)

        try:
            item = next(self._iter)
        except StopIteration:
            pytest.fail(f"there is not enough requests in the {self.cassette_file=}")

        if response_type == 'unary':
            response = item['response']
            assert not isinstance(response, list)
            return self.read_proto_object(response)

        if response_type == 'stream':
            response_stream = item['response_stream']
            assert isinstance(response_stream, list)
            return [
                self.read_proto_object(r)
                for r in response_stream
            ]

        raise NotImplementedError(response_type)


class CassetteMixin:
    def __init__(self, cassette_manager: CassetteManager):
        self.cassette_manager = cassette_manager

    @property
    def generate(self) -> bool:
        return self.cassette_manager.mode == 'write'

    @property
    def write(self):
        return self.cassette_manager.write

    @property
    def read_next(self):
        return self.cassette_manager.read_next

    @property
    def assert_for_grpc(self):
        return self.cassette_manager.assert_for_grpc


class AsyncUnaryUnaryClientInterceptor(aio.UnaryUnaryClientInterceptor, CassetteMixin):
    async def intercept_unary_unary(self, continuation, client_call_details, request):
        self.assert_for_grpc()

        if self.generate:
            call = await continuation(client_call_details, request)
            response = await call
            self.write(request, response)
            return response

        return self.cassette_manager.read_next('unary', request)


class PersistentResponseStream(aio.UnaryStreamCall, aio.Call):
    """
    Stream that masking itself as UnaryStreamCall with __aiter__.

    __aiter__ required for actual work, and it is required to be Call
    descendant for right grpc lib wrapping.
    """

    def __init__(self, items):
        self.items = items
        self._cancelled = False

    async def __aiter__(self):  # pylint: disable=invalid-overridden-method
        for value in self.items:
            yield value

    async def read(self):
        raise NotImplementedError()

    def add_done_callback(self, *args, **kwargs):
        raise NotImplementedError()

    def cancelled(self):
        return self._cancelled

    def done(self):
        return True

    def cancel(self):
        self._cancelled = True

    async def code(self):
        return 0

    async def details(self):
        return ''

    async def wait_for_connection(self):
        return

    async def initial_metadata(self):
        raise NotImplementedError()

    def time_remaining(self):
        raise NotImplementedError()

    async def trailing_metadata(self):
        raise NotImplementedError()


class AsyncUnaryStreamClientInterceptor(aio.UnaryStreamClientInterceptor, CassetteMixin):
    async def intercept_unary_stream(self, continuation, client_call_details, request):
        self.assert_for_grpc()

        if self.generate:
            response_stream = await continuation(client_call_details, request)
            responses = []
            async for response in response_stream:
                responses.append(response)

            self.write(request, responses)

            return PersistentResponseStream(responses)

        # NB: we can't just yield responses from here, because grpc wrapper
        # expecting an awaitable object, not an async generator.
        return PersistentResponseStream(
            self.read_next('stream', request)
        )
