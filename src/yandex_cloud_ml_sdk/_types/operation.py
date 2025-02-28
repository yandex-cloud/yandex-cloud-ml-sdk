# pylint: disable=protected-access
from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, Iterable, TypeVar, cast

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation
# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_service_pb2 import CancelOperationRequest, GetOperationRequest
from yandex.cloud.operation.operation_service_pb2_grpc import OperationServiceStub

from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._utils.sync import run_sync
from yandex_cloud_ml_sdk.exceptions import RunError, WrongAsyncOperationStatusError

from .result import BaseResult

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

logger = get_logger(__name__)

AnyResultTypeT_co = TypeVar('AnyResultTypeT_co', covariant=True)
ResultTypeT_co = TypeVar('ResultTypeT_co', covariant=True)


@dataclass(frozen=True)
class OperationErrorInfo:
    code: int
    message: str
    details: Iterable[str] | None


@dataclass(frozen=True)
class OperationStatus:
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

    @property
    def name(self) -> str:
        if self.is_succeeded:
            return 'success'
        if self.is_failed:
            return 'failed'
        return 'runnning'

    def __repr__(self) -> str:
        error_text = ''
        if self.is_failed:
            error_text = f', error={self.error}'

        return f'{self.__class__.__name__}<{self.name}{error_text}>'


class OperationInterface(abc.ABC, Generic[AnyResultTypeT_co]):
    id: str

    @abc.abstractmethod
    async def _get_status(self, *, timeout: float = 60) -> OperationStatus:
        pass

    @abc.abstractmethod
    async def _get_result(self, *, timeout: float = 60) -> AnyResultTypeT_co:
        pass

    async def _sleep_impl(self, delay: float) -> None:
        # method is created for patching it in a tests
        await asyncio.sleep(delay)

    async def _wait_impl(self, timeout: float, poll_interval: float) -> OperationStatus:
        status = await self._get_status(timeout=timeout)
        while status.is_running:
            logger.debug(
                "Operation %s have non-terminal status %s, sleep for %fs",
                self.id, status.name, poll_interval
            )
            await self._sleep_impl(poll_interval)
            status = await self._get_status(timeout=timeout)

        if status.is_succeeded:
            logger.info('Operation %s successfully finished', self.id)
        else:
            logger.warning('Operation %s failed with status %s', self.id, status)

        return status

    async def _wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> AnyResultTypeT_co:
        logger.info(
            "Starting operation %s polling with a poll interval %fs and poll timeout %fs",
            self.id, poll_interval, poll_timeout,
        )

        coro = self._wait_impl(timeout=timeout, poll_interval=poll_interval)
        if poll_timeout:
            coro = asyncio.wait_for(coro, timeout=poll_timeout)

        await coro

        logger.info("Operation %s polling finished", self.id)

        return await self._get_result(timeout=timeout)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<id="{self.id}">'


class BaseOperation(Generic[ResultTypeT_co], OperationInterface[ResultTypeT_co]):
    _last_known_status: OperationStatus | None

    def __init__(
        self,
        *,
        sdk: BaseSDK,
        id: str,
        result_type: type[ResultTypeT_co],
        proto_result_type: Any,
        service_name: str | None = None,
        transformer: None | Callable[[Any, float], Awaitable[ResultTypeT_co]] = None,
        default_poll_timeout: int = 3600,
    ):  # pylint: disable=redefined-builtin
        self._id = id
        self._sdk = sdk
        self._result_type = result_type
        self._proto_result_type = proto_result_type
        self._last_known_status = None
        self._service_name = service_name
        self._transformer = transformer or self._default_result_transofrmer
        self._default_poll_timeout = default_poll_timeout

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
        # which are BaseResult-compatible, but I don't know how to express it with typing,
        # maybe we need special operation class, which support transforming (probably a base one)
        assert isinstance(self._result_type, BaseResult)

        # NB: mypy can't figure out that self._result_type._from_proto is
        # returning instance of self._result_type which is also is a ResultTypeT_co
        return cast(
            ResultTypeT_co,
            self._result_type._from_proto(proto=proto, sdk=self._sdk)
        )

    @property
    def id(self):
        return self._id

    @property
    def _client(self):
        return self._sdk._client

    async def _get_status(self, *, timeout: float = 60) -> OperationStatus:
        logger.debug('Fetching operation %s status', self.id)
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
            logger.debug('Operation %s have status %s', self.id, status)
            logger.log(TRACE, 'Operation %s have status %s (%s)', self.id, status, response)
            return status

    async def _get_result(self, *, timeout: float = 60) -> ResultTypeT_co:
        logger.debug("Getting operation result for operation %s", self.id)
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
                f"operation {self.id} is running and therefore can't return a result"
            )

        raise WrongAsyncOperationStatusError(
            f"operation {self.id} is done but response have result neither error fields set"
        )

    async def _cancel(self, *, timeout: float = 60) -> OperationStatus:
        logger.debug('Cancelling operation %s', self.id)
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
            self._last_known_status = status = OperationStatus._from_proto(proto=response)
            logger.info('Operation %s successfully canceled', self.id)
            return status

    async def _wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float = 10,
    ) -> ResultTypeT_co:
        poll_timeout = poll_timeout or self._default_poll_timeout
        return await super()._wait(
            timeout=timeout,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )


class AsyncOperation(BaseOperation[ResultTypeT_co]):
    async def get_status(self, *, timeout: float = 60) -> OperationStatus:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> ResultTypeT_co:
        return await self._get_result(timeout=timeout)

    async def cancel(self, *, timeout: float = 60) -> OperationStatus:
        return await self._cancel(timeout=timeout)

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float = 10,
    ) -> ResultTypeT_co:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def __await__(self):
        return self.wait().__await__()


class Operation(BaseOperation[ResultTypeT_co]):
    __get_status = run_sync(BaseOperation._get_status)
    __get_result = run_sync(BaseOperation._get_result)
    __wait = run_sync(BaseOperation._wait)
    __cancel = run_sync(BaseOperation._cancel)

    def get_status(self, *, timeout: float = 60) -> OperationStatus:
        return self.__get_status(timeout=timeout)

    def get_result(self, *, timeout: float = 60) -> ResultTypeT_co:
        return self.__get_result(timeout=timeout)

    def cancel(self, *, timeout: float = 60) -> OperationStatus:
        return self.__cancel(timeout=timeout)

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int | None = None,
        poll_interval: float = 10,
    ) -> ResultTypeT_co:
        return self.__wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )


OperationTypeT = TypeVar('OperationTypeT', bound=BaseOperation)

# this is needed to be able to declare Generic[OperationTypeT] in a dataclasses
class ReturnsOperationMixin(Generic[OperationTypeT]):
    _operation_impl: type[OperationTypeT]
