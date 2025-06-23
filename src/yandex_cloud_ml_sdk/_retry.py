from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterable, Iterable, Literal, cast

import grpc
import grpc.aio
from grpc.aio._typing import RequestType, ResponseType
from typing_extensions import TypeAlias, overload

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from typing import Callable


class RetryKind(Enum):
    """Enum used in "client" code for marking retry policy for specific for each distinct call."""

    NONE = 1  # This call must be not retried
    SINGLE = 2  # This call will be retried as a single entity
    CONTINUATION = 3  # This call will be retried with a continuation mechanism


RETRY_KIND_METADATA_KEY = 'yc-ml-sdk-retry'

UnaryUnaryCallType: TypeAlias = grpc.aio.UnaryUnaryCall[RequestType, ResponseType]
UnaryStreamCallType: TypeAlias = grpc.aio.UnaryStreamCall[RequestType, ResponseType]
UnaryUnaryContinuationType: TypeAlias = (
    'Callable[[grpc.aio.ClientCallDetails, RequestType], Awaitable[UnaryUnaryCallType]]'
)
# NB: I am really believe that there are wrong typing hints in grpc itself:
# there are noted that continuation returning UnaryStreamCallType, but it is not true,
# because in real life it returning a coroutine which returning UnaryStreamCallType
UnaryStreamContinuationType: TypeAlias = (
    'Callable[[grpc.aio.ClientCallDetails, RequestType], Awaitable[UnaryStreamCallType]]'
)
RetrierYieldType: TypeAlias = 'tuple[grpc.aio.Call, ResponseType]'
RetrierReturnType: TypeAlias = 'AsyncIterable[RetrierYieldType]'


class UnaryStreamCallResponseIterator(grpc.aio.UnaryStreamCall):
    """
    UnaryStreamCall wrapper for a AsyncIterable produced by UnaryStreamRetryInterceptor.

    This class is "inspired" by grpc.aio._interceptors.UnaryStreamCallResponseIterator,
    but we can't inherit it becaise it is not part of gprc api.

    So, global problem is, in case if user are using only one grpc.aio.UnaryStreamInterceptor,
    and this interceptor is returning AsyncIterator instead of UnaryStreamCall, everything
    breaks in this place:
    https://github.com/grpc/grpc/blob/b0e5f3b59886c16ad9277c11e7cfcb68713e3c86/src/python/grpcio/grpc/aio/_interceptor.py#L790
    so we are compelled to use our own UnaryStreamCall-wrapper, like this class.

    Also, this class is adapted to work with retries, and it will change underlying call object
    in case of retry, and it will send all required calls like cancel to a proper underlying call object.

    """

    def __init__(
        self,
        response_iterator: AsyncIterable[ResponseType],
    ) -> None:
        self._response_iterator = response_iterator
        self._call: grpc.aio.UnaryStreamCall | None = None

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

    # NB: this method returning Optional[Metadata] in original
    # grpc.aio._interceptors.UnaryStreamCallResponseIterator, despite it is
    # not-optional in grpc.aio.UnaryStreamCall, so I guess it is okay
    # to ignore mypy-override here
    async def initial_metadata(self) -> grpc.aio.Metadata | None:  # type: ignore[override]
        if self._call:
            return await self._call.initial_metadata()
        return None

    async def trailing_metadata(self) -> grpc.aio.Metadata | None:  # type: ignore[override]
        if self._call:
            return await self._call.trailing_metadata()
        return None

    async def code(self) -> grpc.StatusCode:
        if self._call:
            return await self._call.code()
        return grpc.StatusCode.UNKNOWN

    async def details(self) -> str:
        if self._call:
            return await self._call.details()
        return ''

    async def __aiter__(self):  # pylint: disable=invalid-overridden-method
        async for call, value in self._response_iterator:
            self._call = call
            yield value

    async def wait_for_connection(self) -> None:
        if self._call:
            return await self._call.wait_for_connection()
        return None

    async def read(self) -> ResponseType:
        raise NotImplementedError()


class RetrierBase:
    _IDEMPOTENCY_TOKEN_METADATA_KEY = "idempotency-key"
    _ATTEMPT_METADATA_KEY = "x-retry-attempt"

    def __init__(self, policy: RetryPolicy):
        self._policy = policy

    @overload
    async def _retry_single(
        self,
        continuation: UnaryUnaryContinuationType,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen: Literal[False],
    ) -> RetrierReturnType:
        # to please mypy gods
        yield cast(RetrierYieldType, None)

    @overload
    async def _retry_single(
        self,
        continuation: UnaryStreamContinuationType,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen: Literal[True],
    ) -> RetrierReturnType:
        # to please mypy gods
        yield cast(RetrierYieldType, None)

    async def _retry_single(
        self,
        continuation,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen,
    ) -> RetrierReturnType:
        if (timeout := client_call_details.timeout) is not None:
            deadline = time.time() + timeout
        else:
            deadline = None

        assert client_call_details.metadata is not None  # it is always is not None because of our client
        client_call_details.metadata[self._IDEMPOTENCY_TOKEN_METADATA_KEY] = str(uuid.uuid4())

        attempt = 0
        max_attempts = self._policy.max_attempts
        infinity = max_attempts < 0
        while max_attempts > attempt or infinity:
            try:
                result: RetrierYieldType
                async for result in self._grpc_call(
                    attempt,
                    deadline,
                    continuation,
                    client_call_details,
                    request,
                    is_async_gen,
                ):
                    yield result
                return
            except grpc.aio.AioRpcError as e:
                attempt += 1
                if attempt == max_attempts:
                    raise

                code = e.code()

                if code not in self._policy.retriable_codes:
                    raise

                await self._policy.sleep(attempt, deadline)

        raise RuntimeError("this should never happened")

    @overload
    async def _grpc_call(
        self,
        attempt: int,
        deadline: float | None,
        continuation: UnaryUnaryContinuationType,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen: Literal[False],
    ) -> RetrierReturnType:
        # to please mypy gods
        yield cast(RetrierYieldType, None)

    @overload
    async def _grpc_call(
        self,
        attempt: int,
        deadline: float | None,
        continuation: UnaryStreamContinuationType,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen: Literal[True],
    ) -> RetrierReturnType:
        # to please mypy gods
        yield cast(RetrierYieldType, None)

    async def _grpc_call(
        self,
        attempt: int,
        deadline: float | None,
        continuation,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
        is_async_gen,
    ) -> RetrierReturnType:
        if attempt > 0:
            assert client_call_details.metadata is not None  # it is always is not None because of our client
            client_call_details.metadata[self._ATTEMPT_METADATA_KEY] = str(attempt)
            if deadline is not None:
                new_timeout = max((deadline - time.time(), 0))

                # client_call_details isthe namedtuple but apparently this nuance is lacking from
                # grpc-stubs package
                client_call_details = client_call_details._replace(timeout=new_timeout)  # type: ignore[attr-defined]

        call = await continuation(client_call_details, request)

        # NB: we are obliged to unwrap call into a data feed here,
        # because it will raise exceptions at first unwrap place
        if is_async_gen:
            async for value in call:
                yield call, value
        else:
            yield (call, await call)


class UnaryUnaryRetryInterceptor(grpc.aio.UnaryUnaryClientInterceptor, RetrierBase):
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuationType,
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
    ) -> ResponseType | grpc.aio.UnaryUnaryCall:
        assert client_call_details.metadata is not None  # it is always is not None because of our client

        # metadata on a client_call_details is mutable, and there should be a problem
        # about in-place modification
        retry_type = client_call_details.metadata[RETRY_KIND_METADATA_KEY]
        del client_call_details.metadata[RETRY_KIND_METADATA_KEY]

        if retry_type == RetryKind.NONE.name:
            return await continuation(client_call_details, request)

        if retry_type == RetryKind.SINGLE.name:
            async for _, result in self._retry_single(continuation, client_call_details, request, is_async_gen=False):
                return result

        raise RuntimeError(f"wrong {retry_type=} for unary unary call")


class UnaryStreamRetryInterceptor(grpc.aio.UnaryStreamClientInterceptor, RetrierBase):
    async def intercept_unary_stream(
        self,
        # NB: look at UnaryStreamContinuationType comment above about type ignoring
        continuation: UnaryStreamContinuationType,  # type: ignore[override]
        client_call_details: grpc.aio.ClientCallDetails,
        request: RequestType,
    ) -> UnaryStreamCallType | AsyncIterable[ResponseType]:
        assert client_call_details.metadata is not None  # it is always is not None because of our client

        # metadata on a client_call_details is mutable, and there should be a problem
        # about in-place modification
        retry_type = client_call_details.metadata[RETRY_KIND_METADATA_KEY]
        del client_call_details.metadata[RETRY_KIND_METADATA_KEY]

        if retry_type == RetryKind.NONE.name:
            stream = await continuation(client_call_details, request)

        elif retry_type == RetryKind.SINGLE.name:
            raw_stream = self._retry_single(continuation, client_call_details, request, is_async_gen=True)
            stream = UnaryStreamCallResponseIterator(raw_stream)

        elif retry_type == RetryKind.CONTINUATION:
            raise NotImplementedError()

        else:
            raise RuntimeError(f"wrong {retry_type=} for unary unary call")

        return stream


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    initial_backoff: float = 1.0
    max_backoff: float = 10.0
    backoff_multiplier: float = 1.5
    jitter: float = 1.0
    retriable_codes: Iterable[grpc.StatusCode] = (
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.RESOURCE_EXHAUSTED
    )

    unary_unary_interceptor_class: type[UnaryUnaryRetryInterceptor] | None = UnaryUnaryRetryInterceptor
    unary_stream_interceptor_class: type[UnaryStreamRetryInterceptor] | None = UnaryStreamRetryInterceptor

    def get_interceptors(self) -> tuple[grpc.aio.ClientInterceptor, ...]:
        klasses = [self.unary_unary_interceptor_class, self.unary_stream_interceptor_class]
        result = tuple(kls(self) for kls in klasses if kls is not None)

        # because grpc typing are not good
        return result  # type: ignore[return-value]

    async def sleep(self, attempt: int, deadline: float | None) -> None:
        # first attempt == 0, so p.initial_backoff * p.backoff_multiplier ** 0 == p.initial_backoff
        backoff = self.initial_backoff * (self.backoff_multiplier ** attempt) + random.uniform(0, self.jitter)
        if deadline is None:
            deadline_timeout = backoff  # just for an use in min()
        else:
            deadline_timeout = deadline - time.time()

        backoff = min((backoff, self.max_backoff, deadline_timeout))
        backoff = max((backoff, 0))
        await asyncio.sleep(backoff)


class NoRetryPolicy(RetryPolicy):
    def __init__(self):
        super().__init__()

    def get_interceptors(self) -> tuple[()]:
        return ()
