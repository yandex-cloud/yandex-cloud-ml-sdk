# pylint: disable=protected-access
from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, ClassVar, Generic, Iterable, TypeVar, cast, get_origin

from google.protobuf.message import Message
from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation
# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_service_pb2 import CancelOperationRequest, GetOperationRequest
from yandex.cloud.operation.operation_service_pb2_grpc import OperationServiceStub

from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._utils.sync import run_sync_impl
from yandex_cloud_ml_sdk.exceptions import RunError, WrongAsyncOperationStatusError

from .proto import ProtoBasedType

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

logger = get_logger(__name__)

AnyResultTypeT_co = TypeVar('AnyResultTypeT_co', covariant=True)
ResultTypeT_co = TypeVar('ResultTypeT_co', covariant=True)


# NB: it couldn't be ABC because it descendants can't inherit from ABC and Enum at the same time
class BaseOperationStatus:
    @property
    def is_running(self) -> bool:
        raise NotImplementedError()

    @property
    def is_succeeded(self) -> bool:
        raise NotImplementedError()

    @property
    def is_failed(self) -> bool:
        raise NotImplementedError()

    @property
    def is_finished(self) -> bool:
        return self.is_succeeded or self.is_failed

    @property
    def status_name(self) -> str:
        if self.is_succeeded:
            return 'success'
        if self.is_failed:
            return 'failed'
        return 'runnning'


@dataclass(frozen=True)
class OperationErrorInfo:
    code: int
    message: str
    details: Iterable[str] | None


@dataclass(frozen=True)
class OperationStatus(BaseOperationStatus):
    done: bool
    error: OperationErrorInfo | None  # TBD: google.rpc.Status
    response: Any | None = field(repr=False)
    metadata: Any | None = field(repr=False)

    @property
    def is_running(self) -> bool:
        return not self.done

    @property
    def is_succeeded(self) -> bool:
        # NB: when failed, there is non-None response, but with error set
        return self.done and bool(self.response) and not self.is_failed

    @property
    def is_failed(self) -> bool:
        # NB: when succeeded, there non-None error, but with code==0
        return bool(self.done and self.error and self.error.code > 0)

    @classmethod
    def _from_proto(cls, *, proto: ProtoOperation) -> Self:
        error: OperationErrorInfo | None = None
        if proto.error and proto.error.code:
            error = OperationErrorInfo(
                code=proto.error.code,
                message=proto.error.message,
                details=[str(d) for d in proto.error.details],
            )

        return cls(
            done=proto.done,
            error=error,
            response=proto.response,
            metadata=proto.metadata
        )

    def __repr__(self) -> str:
        error_text = ''
        if self.is_failed:
            error_text = f', error={self.error}'

        return f'{self.__class__.__name__}<{self.status_name}{error_text}>'


OperationStatusTypeT = TypeVar('OperationStatusTypeT', bound=BaseOperationStatus)


class OperationInterface(abc.ABC, Generic[AnyResultTypeT_co, OperationStatusTypeT]):
    id: str
    _default_poll_timeout: ClassVar[int] = 3600
    _default_poll_interval: ClassVar[float] = 10
    _custom_default_poll_timeout: int | None = None
    _sdk: BaseSDK

    @abc.abstractmethod
    async def _get_status(self, *, timeout: float = 60) -> OperationStatusTypeT:
        pass

    @abc.abstractmethod
    async def _get_result(self, *, timeout: float = 60) -> AnyResultTypeT_co:
        pass

    @abc.abstractmethod
    async def _cancel(self, *, timeout: float = 60) -> None:
        pass

    async def _sleep_impl(self, delay: float) -> None:
        # method is created for patching it in a tests
        await asyncio.sleep(delay)

    async def _wait_impl(self, timeout: float, poll_interval: float) -> OperationStatusTypeT:
        status = await self._get_status(timeout=timeout)
        while status.is_running:
            logger.debug(
                "%s have non-terminal status %s, sleep for %fs",
                self, status.status_name, poll_interval
            )
            await self._sleep_impl(poll_interval)
            status = await self._get_status(timeout=timeout)

        if status.is_succeeded:
            logger.info('%s successfully finished', self)
        else:
            logger.warning('%s failed with status %s', self, status)

        return status

    async def _wait(
        self,
        *,
        timeout: float,
        poll_timeout: int | None,
        poll_interval: float | None,
    ) -> AnyResultTypeT_co:
        # poll_timeout got from user
        # custom_default_poll_timeout - from operation __init__
        # default_poll_timeout - from class
        poll_timeout = poll_timeout or self._custom_default_poll_timeout or self._default_poll_timeout
        poll_interval = poll_interval or self._default_poll_interval

        logger.info(
            "Starting %s polling with a poll interval %fs and poll timeout %fs",
            self, poll_interval, poll_timeout,
        )

        coro = self._wait_impl(timeout=timeout, poll_interval=poll_interval)
        if poll_timeout:
            coro = asyncio.wait_for(coro, timeout=poll_timeout)

        await coro

        logger.info("%s polling finished", self)

        return await self._get_result(timeout=timeout)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<id="{self.id}">'


class BaseOperation(Generic[ResultTypeT_co], OperationInterface[ResultTypeT_co, OperationStatus]):
    _last_known_status: OperationStatus | None

    def __init__(
        self,
        *,
        sdk: BaseSDK,
        id: str,
        result_type: type[ResultTypeT_co],
        proto_result_type: Any,
        proto_metadata_type: type[Message] | None = None,
        initial_operation: ProtoOperation | None = None,
        service_name: str | None = None,
        transformer: None | Callable[[Any, float], Awaitable[ResultTypeT_co]] = None,
        custom_default_poll_timeout: int = 3600,
    ):  # pylint: disable=redefined-builtin
        self._id = id
        self._sdk = sdk
        self._result_type = result_type
        self._proto_result_type = proto_result_type
        self._proto_metadata_type = proto_metadata_type
        self._service_name = service_name
        self._transformer = transformer or self._default_result_transofrmer
        self._custom_default_poll_timeout = custom_default_poll_timeout

        self._last_known_status = None
        if initial_operation:
            status = self._last_known_status = OperationStatus._from_proto(proto=initial_operation)
            self._on_new_status(status)

    def __repr__(self) -> str:
        arg_list = [
            ('id', repr(self.id)),
            ('result_type', self._result_type.__name__)
        ]
        if self._service_name:
            arg_list.append(('endpoint_name', self._service_name))

        args = ', '.join('='.join((k, v)) for k, v in arg_list)
        return f'{self.__class__.__name__}<{args}>'

    # pylint: disable=unused-argument
    async def _default_result_transofrmer(self, proto: Any, timeout: float) -> ResultTypeT_co:
        # NB: default_result_transformer should be used only with _result_type
        # which are BaseProtoResult-compatible, but I don't know how to express it with typing,
        # maybe we need special operation class, which support transforming (probably a base one)
        # NB: issubclass don't like if instead of SomeClass object pass SomeClass[T];
        # because we use _result_type also for a generic typing reasons, sometimes it requires
        # unwrapping for issubclass check
        result_type = get_origin(self._result_type) or self._result_type
        assert issubclass(result_type, ProtoBasedType), f'{self._result_type} is not ProtoBasedType'

        # NB: mypy can't figure out that self._result_type._from_proto is
        # returning instance of self._result_type which is also is a ResultTypeT_co
        return cast(
            ResultTypeT_co,
            self._result_type._from_proto(proto=proto, sdk=self._sdk)  # type: ignore[attr-defined]
        )

    @property
    def id(self):
        return self._id

    @property
    def _client(self):
        return self._sdk._client

    async def _get_last_known_status(self, *, timeout: float) -> OperationStatus:
        if self._last_known_status is None:
            return await self._get_status(timeout=timeout)

        return self._last_known_status

    def _on_new_status(self, status: OperationStatus) -> None:
        if status.metadata and self._proto_metadata_type:
            metadata = self._parse_metadata(status)
            self._on_new_metadata(metadata)

    def _on_new_metadata(self, metadata: Message) -> None:
        pass

    async def _get_status(self, *, timeout: float = 60) -> OperationStatus:
        logger.debug('Fetching %s status', self)
        request = GetOperationRequest(operation_id=self.id)
        async with self._client.get_service_stub(
            OperationServiceStub,
            timeout=timeout,
            service_name=self._service_name,
        ) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
            self._last_known_status = status = OperationStatus._from_proto(proto=response)
            self._on_new_status(status)
            logger.debug('%s have status %s', self, status)
            logger.log(TRACE, '%s have status %s (%s)', self, status, response)
            return status

    def _parse_metadata(self, status: OperationStatus) -> Message:
        assert self._proto_metadata_type
        assert status.metadata
        metadata = self._proto_metadata_type()
        status.metadata.Unpack(metadata)
        return metadata

    async def _get_result(self, *, timeout: float = 60) -> ResultTypeT_co:
        logger.debug("Getting result for %s", self)
        status = self._last_known_status
        if status is None:
            status = await self._get_status(timeout=timeout)

        if status.is_succeeded:
            assert status.response is not None
            proto_result = self._proto_result_type()
            status.response.Unpack(proto_result)

            return await self._transformer(proto_result, timeout)

        if status.is_failed:
            assert status.error is not None
            raise RunError.from_proro_status(status.error, operation_id=self.id)

        if status.is_running:
            raise WrongAsyncOperationStatusError(
                f"{self} is running and therefore can't return a result"
            )

        raise WrongAsyncOperationStatusError(
            f"{self} is done but response have result neither error fields set"
        )

    async def _cancel(self, *, timeout: float = 60) -> None:
        logger.debug('Cancelling %s', self)
        request = CancelOperationRequest(operation_id=self.id)
        async with self._client.get_service_stub(
            OperationServiceStub,
            timeout=timeout,
            service_name=self._service_name,
        ) as stub:
            response = await self._client.call_service(
                stub.Cancel,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
            self._last_known_status = OperationStatus._from_proto(proto=response)
            logger.info('%s successfully canceled', self)

    async def _wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> ResultTypeT_co:
        return await super()._wait(
            timeout=timeout,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )


class AsyncOperationMixin(OperationInterface[AnyResultTypeT_co, OperationStatusTypeT]):
    async def get_status(self, *, timeout: float = 60) -> OperationStatusTypeT:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> AnyResultTypeT_co:
        return await self._get_result(timeout=timeout)

    async def cancel(self, *, timeout: float = 60) -> None:
        await self._cancel(timeout=timeout)

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> AnyResultTypeT_co:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def __await__(self):
        return self.wait().__await__()


class AsyncOperation(AsyncOperationMixin[ResultTypeT_co, OperationStatus], BaseOperation[ResultTypeT_co]):
    pass


class SyncOperationMixin(OperationInterface[AnyResultTypeT_co, OperationStatusTypeT]):
    def get_status(self, *, timeout: float = 60) -> OperationStatusTypeT:
        return run_sync_impl(
            self._get_status(timeout=timeout),
            self._sdk
        )

    def get_result(self, *, timeout: float = 60) -> AnyResultTypeT_co:
        return run_sync_impl(
            self._get_result(timeout=timeout),
            self._sdk,
        )

    def cancel(self, *, timeout: float = 60) -> None:
        run_sync_impl(
            self._cancel(timeout=timeout),
            self._sdk
        )

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> AnyResultTypeT_co:
        return run_sync_impl(
            self._wait(
                timeout=timeout,
                poll_timeout=poll_timeout,
                poll_interval=poll_interval,
            ),
            self._sdk
        )


class Operation(SyncOperationMixin[ResultTypeT_co, OperationStatus], BaseOperation[ResultTypeT_co]):
    pass


OperationTypeT = TypeVar('OperationTypeT', bound=BaseOperation)

# this is needed to be able to declare Generic[OperationTypeT] in a dataclasses
class ReturnsOperationMixin(Generic[OperationTypeT]):
    _operation_impl: type[OperationTypeT]
