# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.datasets import DatasetType, coerce_dataset_id
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .operation import AsyncBatchTaskOperation, BatchTaskOperation, BatchTaskOperationTypeT

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .model import BaseModelBatchMixin

logger = get_logger(__name__)


class BaseBatchSubdomain(Generic[BatchTaskOperationTypeT], metaclass=abc.ABCMeta):
    def __init__(self, model: BaseModelBatchMixin, sdk: BaseSDK):
        self._model = model
        self._sdk = sdk

    @property
    def _operation_impl(self) -> type[BatchTaskOperationTypeT]:
        return cast(
            type[BatchTaskOperationTypeT],
            self._sdk.batch._operation_impl,
        )

    async def _run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchTaskOperationTypeT:
        dataset_id = coerce_dataset_id(dataset)

        m = self._model
        request = m._make_batch_request(dataset_id)
        stub_class = m._batch_service_stub
        proto_metadata_type = m._batch_proto_metadata_type

        logger.info(
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


class AsyncBatchSubdomain(BaseBatchSubdomain[AsyncBatchTaskOperation]):
    _operation_impl = AsyncBatchTaskOperation

    async def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> AsyncBatchTaskOperation:
        return await self._run_deferred(dataset=dataset, timeout=timeout)


class BatchSubdomain(BaseBatchSubdomain[BatchTaskOperation]):
    _operation_impl = BatchTaskOperation

    __run_deferred = run_sync(BaseBatchSubdomain[BatchTaskOperation]._run_deferred)

    def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchTaskOperation:
        return cast(
            BatchTaskOperation,
            self.__run_deferred(dataset=dataset, timeout=timeout)
        )


BatchSubdomainTypeT = TypeVar('BatchSubdomainTypeT', bound=BaseBatchSubdomain)
