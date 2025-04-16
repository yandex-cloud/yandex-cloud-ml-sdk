# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.datasets import DatasetType, coerce_dataset_id
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .operation import AsyncBatchOperation, BatchOperation, BatchOperationTypeT

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .model import BaseModelBatchMixin

logger = get_logger(__name__)


class BaseBatchSubdomain(Generic[BatchOperationTypeT], metaclass=abc.ABCMeta):
    _operation_impl: type[BatchOperationTypeT]

    def __init__(self, model: BaseModelBatchMixin, sdk: BaseSDK):
        self._model = model
        self._sdk = sdk

    async def _run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchOperationTypeT:
        dataset_id = coerce_dataset_id(dataset)

        m = self._model
        request = m._make_batch_request(dataset_id)
        stub_class = m._batch_service_stub
        proto_result_type = m._batch_proto_result_type
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

        logger.debug('batch task created, resulting operation: %r', response)

        return self._operation_impl(
            id=response.id,
            sdk=self._sdk,
            proto_result_type=proto_result_type,
            proto_metadata_type=proto_metadata_type,
            initial_operation=response,
        )


class AsyncBatchSubdomain(BaseBatchSubdomain[AsyncBatchOperation]):
    _operation_impl = AsyncBatchOperation

    async def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> AsyncBatchOperation:
        return await self._run_deferred(dataset=dataset, timeout=timeout)


class BatchSubdomain(BaseBatchSubdomain[BatchOperation]):
    _operation_impl = BatchOperation

    __run_deferred = run_sync(BaseBatchSubdomain[BatchOperation]._run_deferred)

    def run_deferred(self, dataset: DatasetType, *, timeout: float = 60) -> BatchOperation:
        return cast(
            BatchOperation,
            self.__run_deferred(dataset=dataset, timeout=timeout)
        )


BatchSubdomainTypeT = TypeVar('BatchSubdomainTypeT', bound=BaseBatchSubdomain)
