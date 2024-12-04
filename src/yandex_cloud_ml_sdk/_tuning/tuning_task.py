# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, TypeVar, cast

from typing_extensions import Self
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    CancelTuningRequest, CancelTuningResponse, DescribeTuningRequest, DescribeTuningResponse, GetMetricsUrlRequest,
    GetMetricsUrlResponse
)
from yandex.cloud.ai.tuning.v1.tuning_service_pb2_grpc import TuningServiceStub
from yandex.cloud.ai.tuning.v1.tuning_task_pb2 import TuningTask as TuningTaskProto

from yandex_cloud_ml_sdk._types.operation import OperationInterface, OperationStatus
from yandex_cloud_ml_sdk._types.resource import BaseResource
from yandex_cloud_ml_sdk._types.result import ProtoMessage
from yandex_cloud_ml_sdk._utils.sync import run_sync
from yandex_cloud_ml_sdk.exceptions import TuningError, WrongAsyncOperationStatusError

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK
    from yandex_cloud_ml_sdk._types.model import ModelTuneMixin


TuningResultTypeT_co = TypeVar('TuningResultTypeT_co', covariant=True, bound='ModelTuneMixin')


class TuningErrorInfo:
    """Tuning service can't report normal errors right now"""

    code = 1
    message = "something wrong"
    details = None


class TuningTaskStatus(OperationStatus):
    @classmethod
    def _from_proto(cls, *, proto: TuningTaskProto) -> TuningTaskStatus:
        done = False
        error = None
        if proto.status == TuningTaskProto.Status.COMPLETED:
            done = True
        elif proto.status == TuningTaskProto.Status.FAILED:
            done = True
            error = TuningErrorInfo()

        return cls(
            done=done,
            error=error,
            response=proto
        )


@dataclass(frozen=True)
class BaseTuningTask(OperationInterface[TuningResultTypeT_co], BaseResource):
    _result_type: type[TuningResultTypeT_co]

    folder_id: str
    created_by: str
    created_at: datetime
    started_at: datetime
    finished_at: datetime

    source_model_uri: str
    target_model_uri: str

    operation_id: str

    async def _get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        request = DescribeTuningRequest(tuning_task_id=self.id)
        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            response = await self._client.call_service(
                stub.Describe,
                request=request,
                timeout=timeout,
                expected_type=DescribeTuningResponse
            )

        return TuningTaskStatus._from_proto(proto=response.tuning_task)

    async def _get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        status = await self._get_status(timeout=timeout)
        if status.is_succeeded:
            response = cast(TuningTaskProto, status.response)
            if not response.target_model_uri:
                raise WrongAsyncOperationStatusError(
                    f"tuning task {self.id} have COMPLETED but empty target_model_uri"
                )

            return self._result_type(
                sdk=self._sdk,
                uri=response.target_model_uri
            )

        if status.is_failed:
            error = cast(TuningErrorInfo, status.error)
            raise TuningError.from_proro_status(error, operation_id=self.id)

        if status.is_running:
            raise WrongAsyncOperationStatusError(
                f"tuning task {self.id} is running and therefore can't return a result"
            )

        raise WrongAsyncOperationStatusError(
            f"tuning task {self.id} is done but response have result neither error fields set"
        )

    async def _cancel(self, *, timeout: float = 60) -> TuningTaskStatus:
        request = CancelTuningRequest(tuning_task_id=self.id)
        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            await self._client.call_service(
                stub.Cancel,
                request=request,
                timeout=timeout,
                expected_type=CancelTuningResponse,
            )

        return await self._get_status(timeout=timeout)

    async def _get_metrics_url(self, *, timeout: float = 60) -> str:
        request = GetMetricsUrlRequest(task_id=self.id)
        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            response = await self._client.call_service(
                stub.GetMetricsUrl,
                request=request,
                timeout=timeout,
                expected_type=GetMetricsUrlResponse,
            )

        return response.load_url

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoMessage,
        sdk: BaseSDK,
        result_type: type[TuningResultTypeT_co] | None = None
    ) -> Self:
        proto = cast(TuningTaskProto, proto)
        assert result_type
        return cls(
            _sdk=sdk,
            _result_type=result_type,
            **cls._kwargs_from_message(proto, sdk=sdk),
        )


class AsyncTuningTask(BaseTuningTask[TuningResultTypeT_co]):
    async def get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        return await self._get_result(timeout=timeout)

    async def cancel(self, *, timeout: float = 60) -> TuningTaskStatus:
        return await self._cancel(timeout=timeout)

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> TuningResultTypeT_co:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    async def get_metrics_url(self, *, timeout: float = 60) -> str:
        return await self._get_metrics_url(timeout=timeout)

    def __await__(self):
        return self.wait().__await__()


class TuningTask(BaseTuningTask[TuningResultTypeT_co]):
    __get_status = run_sync(BaseTuningTask._get_status)
    __get_result = run_sync(BaseTuningTask._get_result)
    __wait = run_sync(BaseTuningTask._wait)
    __cancel = run_sync(BaseTuningTask._cancel)
    __get_metrics_url = run_sync(BaseTuningTask._get_metrics_url)

    def get_status(self, *, timeout: float = 60) -> TuningTaskStatus:
        return self.__get_status(timeout=timeout)

    def get_result(self, *, timeout: float = 60) -> TuningResultTypeT_co:
        return self.__get_result(timeout=timeout)

    def cancel(self, *, timeout: float = 60) -> TuningTaskStatus:
        return self.__cancel(timeout=timeout)

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 3600,
        poll_interval: float = 10,
    ) -> TuningResultTypeT_co:
        result = self.__wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )
        return cast(TuningResultTypeT_co, result)

    def get_metrics_url(self, *, timeout: float = 60) -> str:
        return self.__get_metrics_url(timeout=timeout)


TuningTaskTypeT = TypeVar('TuningTaskTypeT', bound=BaseTuningTask)
