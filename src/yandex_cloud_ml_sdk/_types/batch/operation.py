# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

from asyncio import Lock
from typing import TYPE_CHECKING, TypeVar

from yandex.cloud.ai.batch_inference.v1.batch_inference_service_pb2 import (
    CancelBatchInferenceRequest, CancelBatchInferenceResponse, DeleteBatchInferenceRequest,
    DeleteBatchInferenceResponse, DescribeBatchInferenceRequest, DescribeBatchInferenceResponse
)
from yandex.cloud.ai.batch_inference.v1.batch_inference_service_pb2_grpc import BatchInferenceServiceStub

from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset, Dataset
from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._types.operation import (
    AsyncOperationMixin, OperationInterface, ResultTypeT_co, SyncOperationMixin
)
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .status import BatchTaskStatus
from .task_info import BatchTaskInfo

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._client import AsyncCloudClient
    from yandex_cloud_ml_sdk._sdk import BaseSDK

logger = get_logger(__name__)


class BaseBatchTaskOperation(OperationInterface[ResultTypeT_co, BatchTaskStatus]):
    _result_type: type[ResultTypeT_co]
    _custom_default_poll_timeout = 60 * 60 * 72  # 72h

    def __init__(
        self,
        *,
        sdk: BaseSDK,
        id: str,
    ):  # pylint: disable=redefined-builtin
        self._id: str = id
        self._sdk = sdk
        self._lock = Lock()

    @property
    def id(self) -> str:  # type: ignore[override]
        return self._id

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    async def _cancel(self, *, timeout: float = 60) -> None:
        logger.debug('Going to cancel batch task %s', self.task_id)
        request = CancelBatchInferenceRequest(task_id=self._id)
        async with self._client.get_service_stub(BatchInferenceServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Cancel, request, timeout=timeout, expected_type=CancelBatchInferenceResponse
            )
        logger.info('Batch task %s cancelled', self.task_id)

    async def _delete(self, *, timeout: float = 60) -> None:
        """Delete batch task from tasks history.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        """

        logger.debug('Going to delete batch task %s', self.task_id)
        request = DeleteBatchInferenceRequest(task_id=self._id)
        async with self._client.get_service_stub(BatchInferenceServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete, request, timeout=timeout, expected_type=DeleteBatchInferenceResponse
            )
        logger.info('Batch task %s deleted', self.task_id)

    async def _get_task_info(self, *, timeout: float = 60) -> BatchTaskInfo:
        """Get detailed batch task info.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :return: task info object with a lot of info fields.
        """

        logger.log(TRACE, 'Going to fetch batch task %s info', self.task_id)
        request = DescribeBatchInferenceRequest(task_id=self.task_id)
        async with self._client.get_service_stub(BatchInferenceServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Describe, request, timeout=timeout, expected_type=DescribeBatchInferenceResponse
            )

        task_info = BatchTaskInfo._from_proto(proto=response.task, sdk=self._sdk)
        logger.debug('Batch task %s info %r fetched', self.task_id, task_info)
        return task_info

    async def _get_status(self, *, timeout: float = 60) -> BatchTaskStatus:
        logger.log(TRACE, 'Going to fetch batch task %s status', self.task_id)
        info = await self._get_task_info(timeout=timeout)
        logger.debug('Batch task %s status %r fetched', self.task_id, info.status)
        return info.status

    async def _get_result(self, *, timeout: float = 60) -> ResultTypeT_co:
        logger.debug('Going to fetch batch task %s result', self.task_id)
        info = await self._get_task_info(timeout=timeout)
        if not info.result_dataset_id:
            raise RuntimeError(f'trying to fetch unset result_dataset_id from batch task {info}')

        result = await self._sdk.datasets._get(info.result_dataset_id, timeout=timeout)
        logger.info('Batch task %s result %r fetched', self.task_id, result)
        return result

    @property
    def task_id(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}'
            f'<{self._id}>'
        )


class AsyncBatchTaskOperation(AsyncOperationMixin[AsyncDataset, BatchTaskStatus], BaseBatchTaskOperation[AsyncDataset]):
    _result_type = AsyncDataset

    @doc_from(BaseBatchTaskOperation._delete)
    async def delete(self, *, timeout: float = 60) -> None:
        return await self._delete(timeout=timeout)

    @doc_from(BaseBatchTaskOperation._get_task_info)
    async def get_task_info(self, *, timeout: float = 60) -> BatchTaskInfo:
        return await self._get_task_info(timeout=timeout)


class BatchTaskOperation(SyncOperationMixin[Dataset, BatchTaskStatus], BaseBatchTaskOperation[Dataset]):
    _result_type = Dataset

    __delete = run_sync(BaseBatchTaskOperation._delete)
    __get_task_info = run_sync(BaseBatchTaskOperation._get_task_info)

    @doc_from(BaseBatchTaskOperation._delete)
    def delete(self, *, timeout: float = 60) -> None:
        return self.__delete(timeout=timeout)

    @doc_from(BaseBatchTaskOperation._get_task_info)
    def get_task_info(self, *, timeout: float = 60) -> BatchTaskInfo:
        return self.__get_task_info(timeout=timeout)


BatchTaskOperationTypeT = TypeVar('BatchTaskOperationTypeT', bound=BaseBatchTaskOperation)
