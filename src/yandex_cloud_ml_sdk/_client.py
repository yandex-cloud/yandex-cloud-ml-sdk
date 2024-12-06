# pylint: disable=too-many-instance-attributes
from __future__ import annotations

import sys
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal, Protocol, Sequence, TypeVar, cast

import grpc
import grpc.aio
import httpx
from google.protobuf.message import Message
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest  # pylint: disable=no-name-in-module
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub

from ._auth import BaseAuth, get_auth_provider
from ._exceptions import AioRpcError
from ._retry import RETRY_KIND_METADATA_KEY, RetryKind, RetryPolicy
from ._utils.lock import LazyLock
from ._utils.proto import service_for_ctor


class StubType(Protocol):
    def __init__(self, channel: grpc.Channel | grpc.aio.Channel) -> None:
        ...


_T = TypeVar('_T', bound=StubType)
_D = TypeVar('_D', bound=Message)


def _get_user_agent() -> str:
    from . import __version__  # pylint: disable=import-outside-toplevel,cyclic-import

    # NB: grpc breaks in case of using \t instead of space
    return (
        f'yandex-cloud-ml-sdk/{__version__} '
        f'python/{sys.version_info.major}.{sys.version_info.minor}'
    )


@asynccontextmanager
async def httpx_client() -> AsyncIterator[httpx.AsyncClient]:
    headers = {'user-agent': _get_user_agent()}
    async with httpx.AsyncClient(headers=headers) as client:
        yield client


class AsyncCloudClient:
    def __init__(
        self,
        *,
        endpoint: str,
        auth: BaseAuth | str | None,
        service_map: dict[str, str],
        interceptors: Sequence[grpc.aio.ClientInterceptor] | None,
        yc_profile: str | None,
        retry_policy: RetryPolicy,
        enable_server_data_logging: bool | None,
        credentials: grpc.ChannelCredentials | None,
    ):
        self._endpoint = endpoint
        self._auth = auth
        self._auth_provider: BaseAuth | None = None
        self._yc_profile = yc_profile

        self._service_map_override: dict[str, str] = service_map
        self._service_map: dict[str, str] = {}

        self._interceptors = (
            (tuple(interceptors) if interceptors else ()) +
            retry_policy.get_interceptors()
        )

        self._channels: dict[type[StubType], grpc.aio.Channel] = {}
        self._endpoints: dict[type[StubType], str] = {}

        self._auth_lock = LazyLock()
        self._channels_lock = LazyLock()

        self._user_agent = _get_user_agent()
        self._enable_server_data_logging = enable_server_data_logging
        self._credentials = credentials

    async def _init_service_map(self, timeout: float):
        metadata = await self._get_metadata(auth_required=False, timeout=timeout, retry_kind=RetryKind.SINGLE)
        channel = self._new_channel(self._endpoint)
        async with channel:
            stub = ApiEndpointServiceStub(channel)
            response = await stub.List(
                ListApiEndpointsRequest(),
                timeout=timeout,
                metadata=metadata,
            )  # type: ignore[misc]
            for endpoint in response.endpoints:
                self._service_map[endpoint.id] = endpoint.address

        # TODO: add a validation for unknown services in override
        self._service_map.update(self._service_map_override)

    async def _get_metadata(
        self,
        *,
        auth_required: bool,
        timeout: float,
        retry_kind: RetryKind = RetryKind.NONE,
    ) -> tuple[tuple[str, str], ...]:
        metadata: tuple[tuple[str, str], ...] = (
            (RETRY_KIND_METADATA_KEY, retry_kind.name),
            ('x-client-request-id', str(uuid.uuid4())),
        )

        if self._enable_server_data_logging is not None:
            enable_server_data_logging = "true" if self._enable_server_data_logging else "false"
            metadata += (
                ("x-data-logging-enabled", enable_server_data_logging),
            )

        if not auth_required:
            return metadata

        if self._auth_provider is None:
            async with self._auth_lock():
                if self._auth_provider is None:
                    self._auth_provider = await get_auth_provider(
                        auth=self._auth,
                        endpoint=self._endpoint,
                        yc_profile=self._yc_profile
                    )

        # in case of self._auth=NoAuth(), it will return None
        # and it is might be okay: for local installations and on-premises
        auth = await self._auth_provider.get_auth_metadata(client=self, timeout=timeout, lock=self._auth_lock())

        if auth:
            return metadata + (auth, )

        return metadata

    def _get_options(self) -> tuple[tuple[str, str], ...]:
        return (
            ("grpc.primary_user_agent", self._user_agent),
        )

    def _new_channel(self, endpoint: str) -> grpc.aio.Channel:
        credentials = self._credentials or grpc.ssl_channel_credentials()
        return grpc.aio.secure_channel(
            endpoint,
            credentials,
            interceptors=self._interceptors,
            options=self._get_options(),
        )

    async def _get_channel(
        self,
        stub_class: type[_T],
        timeout: float,
        service_name: str | None = None,
    ) -> grpc.aio.Channel:
        if stub_class in self._channels:
            return self._channels[stub_class]

        async with self._channels_lock():
            if stub_class in self._channels:
                return self._channels[stub_class]

            service_name = service_name if service_name else service_for_ctor(stub_class)
            if not self._service_map:
                await self._init_service_map(timeout=timeout)

            if not (endpoint := self._service_map.get(service_name)):
                # NB: this fix will work if service_map will change ai-assistant to ai-assistants
                # (and retrospectively if user will stuck with this version)
                # and if _service_for_ctor will change ai-assistants to ai-assistant
                if service_name in ('ai-assistant', 'ai-assistants'):
                    service_name = 'ai-assistant' if service_name == 'ai-assistants' else 'ai-assistants'
                    if not (endpoint := self._service_map.get(service_name)):
                        raise ValueError(f'failed to find endpoint for {service_name=} and {stub_class=}')
                else:
                    raise ValueError(f'failed to find endpoint for {service_name=} and {stub_class=}')

            self._endpoints[stub_class] = endpoint
            channel = self._channels[stub_class] = self._new_channel(endpoint)
            return channel

    @asynccontextmanager
    async def get_service_stub(
        self,
        stub_class: type[_T],
        timeout: float,
        service_name: str | None = None
    ) -> AsyncIterator[_T]:
        # NB: right now get_service_stub is asynccontextmanager and it is unnecessary,
        # but in future if we will make some ChannelPool, it could be handy to know,
        # when "user" releases resource
        channel = await self._get_channel(stub_class, timeout, service_name=service_name)
        try:
            yield stub_class(channel)
        except grpc.aio.AioRpcError as original:
            # .with_traceback(...) from None allows to mimic
            # original exception without increasing traceback with an
            # extra info, like
            # "During handling of the above exception, another exception occurred"
            # or # "The above exception was the direct cause of the following exception"
            raise AioRpcError.from_base_rpc_error(
                original,
                endpoint=self._endpoints[stub_class],
                auth=self._auth_provider,
                stub_class=stub_class,
            ).with_traceback(original.__traceback__) from None

    async def call_service_stream(
        self,
        service: grpc.aio.UnaryStreamMultiCallable | grpc.UnaryStreamMultiCallable,
        request: Message,
        timeout: float,
        expected_type: type[_D],  # pylint: disable=unused-argument
        auth: bool = True,
        retry_kind: Literal[RetryKind.NONE, RetryKind.SINGLE, RetryKind.CONTINUATION] = RetryKind.SINGLE,
    ) -> AsyncIterator[_D]:
        # NB: when you instantiate a stub class on a async or sync channel, you got
        # "async" of "sync" stub, and it have relevant methods like __aiter__
        # and such. But from typing perspective it have no difference,
        # it just a stub object.
        # Auto-generated stubs for grpc saying, that attribute stub.Service returns
        # grpc.Unary...Multicallable, not async one, but in real life
        # we are using only async stubs in this project.
        # In ideal world we need to do something like
        # cast(grpc.aio.UnaryStreamMultiCallable, stub.Service) at usage place,
        # but it is too lot places to insert this cast, so I'm doing it here.
        service = cast(grpc.aio.UnaryStreamMultiCallable, service)

        metadata = await self._get_metadata(auth_required=auth, timeout=timeout, retry_kind=retry_kind)
        call = service(request, metadata=metadata, timeout=timeout)

        try:
            async for response in call:
                yield cast(_D, response)
        except GeneratorExit:
            call.cancel()
            raise

    async def call_service(
        self,
        service: grpc.aio.UnaryUnaryMultiCallable | grpc.UnaryUnaryMultiCallable,
        request: Message,
        timeout: float,
        expected_type: type[_D],  # pylint: disable=unused-argument
        auth: bool = True,
        retry_kind: Literal[RetryKind.NONE, RetryKind.SINGLE] = RetryKind.SINGLE,
    ) -> _D:
        service = cast(grpc.aio.UnaryUnaryMultiCallable, service)

        metadata = await self._get_metadata(auth_required=auth, timeout=timeout, retry_kind=retry_kind)
        result = await service(
            request,
            metadata=metadata,
            timeout=timeout,
            wait_for_ready=True,
        )
        return cast(_D, result)
