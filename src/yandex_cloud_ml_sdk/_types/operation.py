# pylint: disable=protected-access
from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation
# pylint: disable-next=no-name-in-module
from yandex.cloud.operation.operation_service_pb2 import CancelOperationRequest, GetOperationRequest
from yandex.cloud.operation.operation_service_pb2_grpc import OperationServiceStub

from yandex_cloud_ml_sdk._utils.sync import run_sync
from yandex_cloud_ml_sdk.exceptions import RunError, WrongAsyncOperationStatusError

from .result import BaseResult

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


ResultTypeT = TypeVar('ResultTypeT', bound=BaseResult)


@dataclass(frozen=True)
class OperationStatus:
    done: bool
    error: Any | None  # TBD: google.rpc.Status
    response: Any | None

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


class OperationInterface(abc.ABC, Generic[ResultTypeT]):
    id: str

    @abc.abstractmethod
    async def _get_status(self, *, timeout: float = 60) -> OperationStatus:
        pass

    @abc.abstractmethod
    async def _get_result(self, *, timeout: float = 60) -> ResultTypeT:
        pass

    async def _sleep_impl(self, delay: float) -> None:
        # method is created for patching it in a tests
        await asyncio.sleep(delay)

    async def _wait_impl(self, timeout: float, poll_interval: float) -> OperationStatus:
        status = await self._get_status(timeout=timeout)
        while status.is_running:
            await self._sleep_impl(poll_interval)
            status = await self._get_status(timeout=timeout)

        return status

    async def _wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> ResultTypeT:
        coro = self._wait_impl(timeout=timeout, poll_interval=poll_interval)
        if poll_timeout:
            coro = asyncio.wait_for(coro, timeout=poll_timeout)

        await coro

        return await self._get_result(timeout=timeout)


class BaseOperation(OperationInterface[ResultTypeT]):
    _last_known_status: OperationStatus | None

    def __init__(self, sdk: BaseSDK, id: str, result_type: type[ResultTypeT]):  # pylint: disable=redefined-builtin
        self._id = id
        self._sdk = sdk
        self._result_type: type[BaseResult] = result_type
        self._last_known_status = None

    @property
    def id(self):
        return self._id

    @property
    def _client(self):
        return self._sdk._client

    async def _get_status(self, *, timeout: float = 60) -> OperationStatus:
        request = GetOperationRequest(operation_id=self.id)
        async with self._client.get_service_stub(OperationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
            self._last_known_status = status = OperationStatus(
                done=response.done,
                error=response.error,
                response=response.response
            )
            return status

    async def _get_result(self, *, timeout: float = 60) -> ResultTypeT:
        status = self._last_known_status
        if status is None:
            status = await self._get_status(timeout=timeout)

        if status.is_succeeded:
            assert status.response is not None
            proto_result = self._result_type._proto_result_type()
            status.response.Unpack(proto_result)

            # NB: mypy can't figure out that self._result_type._from_proto is
            # returning instance of self._result_type which is also is a ResultTypeT
            return cast(ResultTypeT, self._result_type._from_proto(proto=proto_result, sdk=self._sdk))

        if status.is_failed:
            assert status.error is not None
            raise RunError.from_proro_status(status.error)

        if status.is_running:
            raise WrongAsyncOperationStatusError(
                f"operation {self.id} is running and therefore can't return a result"
            )

        raise WrongAsyncOperationStatusError(
            f"operation {self.id} is done but response have result neither error fields set"
        )

    async def _cancel(self, *, timeout: float = 60) -> OperationStatus:
        request = CancelOperationRequest(operation_id=self.id)
        async with self._client.get_service_stub(OperationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Cancel,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
            self._last_known_status = status = OperationStatus(
                done=response.done,
                error=response.error,
                response=response.response
            )
            return status

    async def _wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> ResultTypeT:
        # NB: mypy doesn't resolve generic type ResultTypeT in case of inheritance,
        # so, just recopy this method here
        return await super()._wait(
            timeout=timeout,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )


class AsyncOperation(BaseOperation[ResultTypeT]):
    async def get_status(self, *, timeout: float = 60) -> OperationStatus:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> ResultTypeT:
        return await self._get_result(timeout=timeout)

    async def cancel(self, *, timeout: float = 60) -> None:
        await self._cancel(timeout=timeout)

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> ResultTypeT:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def __await__(self):
        return self.wait().__await__()


class Operation(BaseOperation[ResultTypeT]):
    __get_status = run_sync(BaseOperation._get_status)
    __get_result = run_sync(BaseOperation._get_result)
    __wait = run_sync(BaseOperation._wait)
    __cancel = run_sync(BaseOperation._cancel)

    def get_status(self, *, timeout: float = 60) -> OperationStatus:
        return self.__get_status(timeout=timeout)

    def get_result(self, *, timeout: float = 60) -> ResultTypeT:
        return self.__get_result(timeout=timeout)

    def cancel(self, *, timeout: float = 60) -> None:
        self.__cancel(timeout=timeout)

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> ResultTypeT:
        return self.__wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )


OperationTypeT = TypeVar('OperationTypeT', bound=BaseOperation)
