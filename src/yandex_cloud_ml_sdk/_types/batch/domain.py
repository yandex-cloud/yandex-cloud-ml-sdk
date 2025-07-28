# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.datasets import DatasetType, coerce_dataset_id
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .operation import AsyncBatchTask, BatchTask, BatchTaskTypeT

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .model import BaseModelBatchMixin

logger = get_logger(__name__)


class BaseBatchSubdomain(Generic[BatchTaskTypeT], metaclass=abc.ABCMeta):
    _operation_impl: type[BatchTaskTypeT]

    def __init__(self, model: BaseModelBatchMixin, sdk: BaseSDK):
        self._model = model
        self._sdk = sdk

    async def _run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchTaskTypeT:
        dataset_id = coerce_dataset_id(dataset)

        m = self._model
        request = m._make_batch_request(dataset_id)
        stub_class = m._batch_service_stub
        proto_metadata_type = m._batch_proto_metadata_type

        logger.debug(
            'going to create batch task at %r service with a %r request',
            stub_class.__name__, request
        )

        async with self._sdk._client.get_service_stub(stub_class, timeout=timeout) as stub:
            response = await self._sdk._client.call_service(
                stub.Completion,
                request=request,
                expected_type=ProtoOperation,
                timeout=timeout
            )

        metadata = proto_metadata_type()
        response.metadata.Unpack(metadata)
        task_id = metadata.task_id

        logger.debug('batch task %s created, resulting operation: %r', task_id, response)

        return self._operation_impl(
            id=task_id,
            sdk=self._sdk,
        )


class AsyncBatchSubdomain(BaseBatchSubdomain[AsyncBatchTask]):
    _operation_impl = AsyncBatchTask

    async def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> AsyncBatchTask:
        return await self._run_deferred(dataset=dataset, timeout=timeout)


class BatchSubdomain(BaseBatchSubdomain[BatchTask]):
    _operation_impl = BatchTask

    __run_deferred = run_sync(BaseBatchSubdomain[BatchTask]._run_deferred)

    def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchTask:
        return cast(
            BatchTask,
            self.__run_deferred(dataset=dataset, timeout=timeout)
        )


BatchSubdomainTypeT = TypeVar('BatchSubdomainTypeT', bound=BaseBatchSubdomain)
