from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from typing import Callable, Generic, Tuple, TypeAlias, TypeVar, Union

import grpc
import grpc.aio
from grpc.aio._typing import RequestType, ResponseType

UnaryUnaryCallType: TypeAlias = grpc.aio.UnaryUnaryCall[RequestType, ResponseType]
UnaryStreamCallType: TypeAlias = grpc.aio.UnaryStreamCall[RequestType, ResponseType]
StreamStreamCallType: TypeAlias = grpc.aio.StreamStreamCall[RequestType, ResponseType]
StreamUnaryCallType: TypeAlias = grpc.aio.StreamUnaryCall[RequestType, ResponseType]
UnaryUnaryContinuationType: TypeAlias = (
    Callable[[grpc.aio.ClientCallDetails, RequestType], Awaitable[UnaryUnaryCallType]]
)
# NB: I am really believe that there are wrong typing hints in grpc itself:
# there are noted that continuation returning UnaryStreamCallType, but it is not true,
# because in real life it returning a coroutine which returning UnaryStreamCallType
UnaryStreamContinuationType: TypeAlias = (
    Callable[[grpc.aio.ClientCallDetails, RequestType], Awaitable[UnaryStreamCallType]]
)
StreamReturnCallType: TypeAlias = Union[
    UnaryStreamCallType[RequestType, ResponseType],
    StreamStreamCallType[RequestType, ResponseType]
]
UnaryReturnCallType: TypeAlias = Union[
    UnaryStreamCallType[RequestType, ResponseType],
    StreamStreamCallType[RequestType, ResponseType],
]

StreamReturnCallTypeT = TypeVar(
    'StreamReturnCallTypeT',
    bound=StreamReturnCallType,
)

WrappedStreamReturnCallType = AsyncIterator[
    tuple[StreamReturnCallTypeT, ResponseType]
]


class StreamResponseIteratorMixin(Generic[StreamReturnCallTypeT, ResponseType]):
    """
    Wrapper for a AsyncIterable produced by Unary/StreamStreamRetryInterceptor.

    This class is "inspired" by grpc.aio._interceptors._StreamCallResponseIterator,,
    but we can't inherit it becaise it is not part of gprc api.

    So, global problem is, in case if user are using only one grpc.aio.UnaryStreamInterceptor,
    and this interceptor is returning AsyncIterator instead of UnaryStreamCall, everything
    breaks in this place:
    https://github.com/grpc/grpc/blob/b0e5f3b59886c16ad9277c11e7cfcb68713e3c86/src/python/grpcio/grpc/aio/_interceptor.py#L790
    so we are compelled to use our own UnaryStreamCall-wrapper, like this class.

    Also, this class is adapted to work with retries, and it will change underlying call object
    in case of retry, and it will send all required calls like cancel to a proper underlying call object.

    """

    _call: StreamReturnCallTypeT | None
    _response_iterator: WrappedStreamReturnCallType[StreamReturnCallTypeT, ResponseType]

    def __init__(
        self,
        call: StreamReturnCallTypeT | None,
        response_iterator: WrappedStreamReturnCallType[StreamReturnCallTypeT, ResponseType],
    ) -> None:
        """
        Unlike _StreamCallResponseIterator, we are using response_iterator not with
        AsyncIterator[ResponseType], but with AsyncIterator[tuple[Call, ResponseType]]
        which are allowing to change underlying call in the middle of iteration.

        It is required for change call object in case of retry.
        """
        self._call = call
        self._response_iterator = response_iterator

    def cancel(self) -> bool:
        if self._call:
            return self._call.cancel()
        return True

    def cancelled(self) -> bool:
        if self._call:
            return self._call.cancelled()
        return True

    def done(self) -> bool:
        if self._call:
            return self._call.done()
        return True

    def add_done_callback(self, callback) -> None:
        raise NotImplementedError()

    def time_remaining(self) -> float | None:
        if self._call:
            return self._call.time_remaining()
        return None

    async def initial_metadata(self) -> grpc.aio.Metadata:
        if self._call:
            return await self._call.initial_metadata()
        return grpc.aio.Metadata()

    async def trailing_metadata(self) -> grpc.aio.Metadata:
        if self._call:
            return await self._call.trailing_metadata()
        return grpc.aio.Metadata()

    async def code(self) -> grpc.StatusCode:
        if self._call:
            return await self._call.code()
        return grpc.StatusCode.UNKNOWN

    async def details(self) -> str:
        if self._call:
            return await self._call.details()
        return ''

    async def __aiter__(self) -> AsyncIterator[ResponseType]:
        async for call, value in self._response_iterator:
            self._call = call
            yield value

    async def __anext__(self) -> ResponseType:
        call, value = await self._response_iterator.__anext__()
        self._call = call
        return value

    async def wait_for_connection(self) -> None:
        if self._call:
            return await self._call.wait_for_connection()
        return None

    async def read(self) -> ResponseType:
        raise NotImplementedError()


# pylint can't see abstract methods realization in mixin
# pylint: disable-next=abstract-method
class UnaryStreamCallResponseIterator(
    Generic[RequestType, ResponseType],
    StreamResponseIteratorMixin[UnaryStreamCallType[RequestType, ResponseType], ResponseType],
    grpc.aio.UnaryStreamCall[RequestType, ResponseType]
):
    pass


# pylint: disable-next=abstract-method
class StreamStreamCallResponseIterator(
    Generic[RequestType, ResponseType],
    StreamResponseIteratorMixin[StreamStreamCallType[RequestType, ResponseType], ResponseType],
    grpc.aio.StreamStreamCall[RequestType, ResponseType],
):
    async def done_writing(self) -> None:
        assert self._call
        await self._call.done_writing()

    async def write(self, request: RequestType) -> None:
        assert self._call
        await self._call.write(request)
