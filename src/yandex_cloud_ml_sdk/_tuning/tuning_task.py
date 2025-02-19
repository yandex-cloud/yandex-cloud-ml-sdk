# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, cast

from grpc import StatusCode
from grpc.aio import AioRpcError
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    DescribeTuningRequest, DescribeTuningResponse, GetMetricsUrlRequest, GetMetricsUrlResponse, TuningMetadata
)
from yandex.cloud.ai.tuning.v1.tuning_service_pb2_grpc import TuningServiceStub
from yandex.cloud.ai.tuning.v1.tuning_task_pb2 import TuningTask as TuningTaskProto
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation
from yandex.cloud.operation.operation_service_pb2 import CancelOperationRequest, GetOperationRequest
from yandex.cloud.operation.operation_service_pb2_grpc import OperationServiceStub

from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._types.operation import OperationErrorInfo, OperationInterface, OperationStatus
from yandex_cloud_ml_sdk._types.resource import BaseResource
from yandex_cloud_ml_sdk._types.result import ProtoMessage
from yandex_cloud_ml_sdk._utils.sync import run_sync
from yandex_cloud_ml_sdk.exceptions import RunError, WrongAsyncOperationStatusError

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK
    from yandex_cloud_ml_sdk._types.model import ModelTuneMixin


logger = get_logger(__name__)
TuningResultTypeT_co = TypeVar('TuningResultTypeT_co', covariant=True, bound='ModelTuneMixin')


class TuningTaskStatusEnum(Enum):
    STATUS_UNSPECIFIED = 0
    CREATED = 1
    PENDING = 2
    IN_PROGRESS = 3
    COMPLETED = 4
    FAILED = 5


@dataclass(frozen=True)
class TuningTaskInfo(BaseResource):
    task_id: str
    operation_id: str

    status: TuningTaskStatusEnum

    folder_id: str
    created_by: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    source_model_uri: str
    target_model_uri: str | None

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessage, sdk: BaseSDK) -> dict[str, Any]:  # pylint: disable=unused-argument
        proto = cast(TuningTaskProto, proto)
        kwargs = super()._kwargs_from_message(proto=proto, sdk=sdk)
        kwargs['status'] = TuningTaskStatusEnum(proto.status)
        return kwargs


class TuningTaskStatus(OperationStatus):
    @classmethod
    def _from_tuning_info(cls, info: TuningTaskInfo) -> TuningTaskStatus:
        done = False
        error = None
        if info.status == TuningTaskStatusEnum.COMPLETED:
            done = True
        elif info.status == TuningTaskStatusEnum.FAILED:
            done = True
            error = OperationErrorInfo(
                code=-1,
                message="smth wrong",
                details=None
            )

        return cls(
            done=done,
            error=error,
            response=info,
            metadata=None,
        )


class BaseTuningTask(OperationInterface[TuningResultTypeT_co]):
    _sdk: BaseSDK

    def __init__(
        self,
        sdk: BaseSDK,
        result_type: type[TuningResultTypeT_co],
        operation_id: str | None,
        task_id: str | None,
    ):
        self._sdk = sdk
        self._result_type = result_type
        self._operation_id = operation_id
        self._task_id = task_id

        if not operation_id and not task_id:
            raise TypeError('tuning task must be created with operation_id either with task_id')

    @property
    def id(self):
        return self._operation_id or self._task_id

    def __repr__(self):
        return f'{self.__class__.__name__}<id={self.id!r}, result_type={self._result_type.__name__}(...)>'

    @property
    def _client(self):
        return self._sdk._client

    async def _get_operation_id(self, *, timeout: float = 60) -> str | None:
        if not self._operation_id:
            logger.debug('Trying to find operation_id for %s', self)
            task_info = await self._get_task_info(timeout=timeout)
            if not task_info:
                logger.debug('Failed to find operation_id for %s', self)
                return None

            self._operation_id = task_info.operation_id
            logger.debug('%s have operation_id=%s', self, self._operation_id)

        return self._operation_id

    async def _get_task_id(self, *, timeout: float = 60) -> str | None:
        if not self._task_id:
            logger.debug('Trying to find tuning_task_id for %s', self)
            status = await self._get_status(timeout=timeout)
            if not status.metadata:
                logger.debug('Failed to find tuning_task_id for %s', self)
                return None

            metadata = TuningMetadata()
            status.metadata.Unpack(metadata)
            self._task_id = metadata.tuning_task_id
            logger.debug('%s have tuning_task_id=%s', self, self._task_id)

        return self._task_id

    async def _get_task_info(self, *, timeout: float = 60) -> TuningTaskInfo | None:
        task_id = await self._get_task_id(timeout=timeout)
        if not task_id:
            logger.debug('Failed to fetch task info for %s due to absence of task', self)
            return None

        logger.debug('Fetching task info for %s', self)
        request = DescribeTuningRequest(tuning_task_id=task_id)
        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            proto = await self._client.call_service(
                stub.Describe,
                request=request,
                timeout=timeout,
                expected_type=DescribeTuningResponse
            )

        task_info = TuningTaskInfo._from_proto(proto=proto.tuning_task, sdk=self._sdk)
        logger.debug('Task info successfully fetched for %s', self)
        logger.log(
            TRACE,
            'Task info task_info %s (%s) successfully fetched for %s',
            task_info, proto.tuning_task, self
        )
        return task_info

    async def _get_operation_status(self, *, timeout: float = 60) -> TuningTaskStatus | None:
        # TODO
        # operation could return 404 in case of trying to get it after 2 weeks;
        # we need to properly process this
        operation_id = await self._get_operation_id(timeout=timeout)
        if not operation_id:
            logger.debug(
                'Failed to fetch operation status for %s due to absence of operation',
                self,
            )
            return None

        logger.debug('Fetching operation status for %s', self)
        request = GetOperationRequest(operation_id=operation_id)
        async with self._client.get_service_stub(
            OperationServiceStub,
            timeout=timeout,
            service_name='ai-foundation-models',
        ) as stub:
            proto = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        status = TuningTaskStatus._from_proto(proto=proto)
        logger.debug('Operation status %s successfully fetched for %s', status, self)
        logger.log(TRACE, 'Operation status %s (%s) successfully fetched for %s', status, proto, self)
        return status

    async def _get_task_status(self, *, timeout: float = 60) -> TuningTaskStatus | None:
        info = await self._get_task_info(timeout=timeout)
        if not info:
            return None

        return TuningTaskStatus._from_tuning_info(info=info)

    async def _get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        logger.debug('Fetching status for %s', self)

        status = await self._get_operation_status()
        if not status:
            status = await self._get_task_status()

        if not status:
            raise WrongAsyncOperationStatusError(
                f'failed to get status for tuning task with {self._task_id=} and {self._operation_id=}'
            )
        logger.debug('%s have status %s', self, status)
        return status

    async def _get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        logger.debug('Getting result for %s', self)
        status = await self._get_status(timeout=timeout)
        if status.is_succeeded:
            info = await self._get_task_info(timeout=timeout)
            if not info or not info.target_model_uri:
                raise WrongAsyncOperationStatusError(
                    f"tuning task {self._task_id} have COMPLETED status but empty target_model_uri"
                )

            return self._result_type(
                sdk=self._sdk,
                uri=info.target_model_uri
            )

        if status.is_failed:
            assert status.error is not None
            raise RunError.from_proro_status(status.error, operation_id=self.id)

        if status.is_running:
            raise WrongAsyncOperationStatusError(
                f"tuning task {self.id} is running and therefore can't return a result"
            )

        raise WrongAsyncOperationStatusError(
            f"tuning task {self.id} is done but response have result neither error fields set"
        )

    async def _cancel(self, *, timeout: float = 60) -> None:
        # TODO: it probably will raise an Exception:
        # 1) after operation done
        # 2) after operation expire

        logger.debug('Cancelling %s', self)
        operation_id = await self._get_operation_id(timeout=timeout)
        if not operation_id:
            raise WrongAsyncOperationStatusError(
                f"failed to cancel tuning task {self.id} because "
                "it already gone from operations storage (few weeks)"
            )

        request = CancelOperationRequest(operation_id=operation_id)
        async with self._client.get_service_stub(
            OperationServiceStub,
            timeout=timeout,
            service_name='ai-foundation-models',
        ) as stub:
            await self._client.call_service(
                stub.Cancel,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
        logger.info('%s successfully cancelled', self)

    async def _get_metrics_url(self, *, timeout: float = 60) -> str | None:
        logger.debug('Fetching metrics url for %s', self)
        task_id = await self._get_task_id(timeout=timeout)
        response: GetMetricsUrlResponse | None = None
        if task_id:
            request = GetMetricsUrlRequest(task_id=task_id)
            async with self._client.get_service_stub(
                TuningServiceStub,
                timeout=timeout,
            ) as stub:
                try:
                    response = await self._client.call_service(
                        stub.GetMetricsUrl,
                        request=request,
                        timeout=timeout,
                        expected_type=GetMetricsUrlResponse,
                    )
                except AioRpcError as e:
                    if e.code() != StatusCode.NOT_FOUND:
                        raise

        if task_id and response and response.load_url:
            logger.debug('Metrics url for %s successfully fetched', self)
            return response.load_url

        logger.debug('Metrics url for %s is not available', self)
        return None


class AsyncTuningTask(BaseTuningTask[TuningResultTypeT_co]):
    async def get_task_info(self, *, timeout: float = 60) -> TuningTaskInfo | None:
        return await self._get_task_info(timeout=timeout)

    async def get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        return await self._get_result(timeout=timeout)

    async def cancel(self, *, timeout: float = 60) -> None:
        await self._cancel(timeout=timeout)

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 10,
    ) -> TuningResultTypeT_co:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    async def get_metrics_url(self, *, timeout: float = 60) -> str | None:
        return await self._get_metrics_url(timeout=timeout)

    def __await__(self):
        return self.wait().__await__()


class TuningTask(BaseTuningTask[TuningResultTypeT_co]):
    __get_status = run_sync(BaseTuningTask._get_status)
    __get_result = run_sync(BaseTuningTask._get_result)
    __wait = run_sync(BaseTuningTask._wait)
    __cancel = run_sync(BaseTuningTask._cancel)
    __get_metrics_url = run_sync(BaseTuningTask._get_metrics_url)
    __get_task_info = run_sync(BaseTuningTask._get_task_info)

    def get_task_info(self, *, timeout: float = 60) -> TuningTaskInfo | None:
        return self.__get_task_info(timeout=timeout)

    def get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        return self.__get_status(timeout=timeout)

    def get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        return self.__get_result(timeout=timeout)

    def cancel(self, *, timeout: float = 60) -> None:
        self.__cancel(timeout=timeout)

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 10,
    ) -> TuningResultTypeT_co:
        result = self.__wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )
        return cast(TuningResultTypeT_co, result)

    def get_metrics_url(self, *, timeout: float = 60) -> str | None:
        return self.__get_metrics_url(timeout=timeout)


TuningTaskTypeT = TypeVar('TuningTaskTypeT', bound=BaseTuningTask)
