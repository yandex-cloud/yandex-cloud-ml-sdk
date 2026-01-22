from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable
from typing import Any, Generic, cast

import grpc
import grpc.aio

from yandex_ai_studio_sdk._utils.grpc import (
    RequestType, ResponseType, StreamReturnCallType, StreamStreamCallResponseIterator, UnaryReturnCallType,
    UnaryStreamCallResponseIterator, WrappedStreamReturnCallType
)

from .utils import get_logger

logger = get_logger(__name__)


def split_full_method(full_method: str | bytes) -> tuple[str, str]:
    # "/package.Service/Method" -> ("package.Service", "Method")
    if isinstance(full_method, bytes):
        method = full_method.decode('utf-8')
    else:
        method = full_method

    if not method or not method.startswith("/"):
        return "", method or ""
    parts = method.lstrip('/').rsplit("/", 1)
    return parts[0], parts[1] if len(parts) > 1 else '<unknown>'


async def maybe_await(x):
    return await x if inspect.isawaitable(x) else x


async def _log_from_call(
    *,
    call: Any,
    full_method: str,
    err: BaseException | None,
    method_type: str
):
    service, method = split_full_method(full_method)
    metadata: dict[str, str] = {}

    # Prefer details from AioRpcError (it always has them)
    if isinstance(err, grpc.aio.AioRpcError):
        code = err.code()
        details = err.details()
        raw_trailing = err.trailing_metadata()
        trailing = None
        if raw_trailing:
            if isinstance(raw_trailing, grpc.aio.Metadata):
                trailing = raw_trailing
            else:
                trailing = [('sdk-wrong-type-of-metadata', repr(raw_trailing))]
    else:
        # Otherwise read from the call object after it finishes.
        # In grpc.aio, these may be either immediate or awaitable depending on version.
        try:
            code = await maybe_await(call.code())
        except Exception:  # pylint: disable=broad-exception-caught
            code = None
        try:
            details = await maybe_await(call.details())
        except Exception:  # pylint: disable=broad-exception-caught
            details = None
        try:
            trailing = await maybe_await(call.trailing_metadata())
        except Exception:  # pylint: disable=broad-exception-caught
            trailing = None

    if trailing:
        # pylint: disable-next=unnecessary-comprehension
        metadata = {key: value for key, value in trailing}

    logger.debug(
        "grpc client %s call service=%s method=%s code=%s details=%r metadata=%r",
        method_type,
        service,
        method,
        code,
        details,
        metadata,
    )


class UnaryReturnCallProxy(Generic[ResponseType]):
    method: str

    def __init__(self, call: UnaryReturnCallType[RequestType, ResponseType], full_method: str):
        self._call = call
        self._full_method = full_method

    def __getattr__(self, name):
        return getattr(self._call, name)

    async def _run(self) -> ResponseType:
        err = None
        try:
            # NB: I dunno why, but mypy can't figure out that UnaryReturnCallType is Awaitable
            result = await cast(Awaitable[ResponseType], self._call)
            return result
        except BaseException as e:
            err = e
            raise
        finally:
            await _log_from_call(
                call=self._call, full_method=self._full_method, err=err, method_type=self.method
            )

    def __await__(self):
        return self._run().__await__()


class _UnaryUnaryCallProxy(UnaryReturnCallProxy):
    method = 'UnaryUnary'


class _StreamUnaryCallProxy(UnaryReturnCallProxy):
    method = 'StreamUnary'


class StreamReturnCallProxy(Generic[RequestType, ResponseType]):
    method: str

    def __init__(self, call: StreamReturnCallType[RequestType, ResponseType], full_method: str):
        self._call = call
        self._full_method = full_method
        self._logged = False

    def __getattr__(self, name):
        return getattr(self._call, name)

    async def _gen(self) -> WrappedStreamReturnCallType[StreamReturnCallType[RequestType, ResponseType], ResponseType]:
        err = None
        try:
            i = 0
            async for item in self._call:
                i += 1
                yield self._call, item
        except BaseException as e:
            err = e
            raise
        finally:
            if not self._logged:
                self._logged = True
                await _log_from_call(
                    call=self._call, full_method=self._full_method, err=err, method_type=self.method,
                )

    def __aiter__(self):
        return self._gen()


class _UnaryStreamCallProxy(StreamReturnCallProxy):
    method = 'UnaryStream'


class _StreamStreamCallProxy(StreamReturnCallProxy):
    method = 'StreamStream'


class UnaryUnaryLogInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    async def intercept_unary_unary(self, continuation, client_call_details, request) -> ResponseType:
        call = await continuation(client_call_details, request)
        return await _UnaryUnaryCallProxy(call, client_call_details.method)


class UnaryStreamLogInterceptor(grpc.aio.UnaryStreamClientInterceptor):
    async def intercept_unary_stream(self, continuation, client_call_details, request) -> AsyncIterator[ResponseType]:
        call = await continuation(client_call_details, request)
        return UnaryStreamCallResponseIterator(call, _UnaryStreamCallProxy(call, client_call_details.method))


class StreamUnaryLogInterceptor(grpc.aio.StreamUnaryClientInterceptor):
    async def intercept_stream_unary(self, continuation, client_call_details, request_iterator) -> ResponseType:
        call = await continuation(client_call_details, request_iterator)
        return await _StreamUnaryCallProxy(call, client_call_details.method)


class StreamStreamLogInterceptor(grpc.aio.StreamStreamClientInterceptor):
    async def intercept_stream_stream(self, continuation, client_call_details, request_iterator) -> AsyncIterator[ResponseType]:
        call = await continuation(client_call_details, request_iterator)
        return StreamStreamCallResponseIterator(call, _StreamStreamCallProxy(call, client_call_details.method))


def get_log_interceprtors():
    return (UnaryUnaryLogInterceptor(), UnaryStreamLogInterceptor(), StreamUnaryLogInterceptor(), StreamStreamLogInterceptor())
