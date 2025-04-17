from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset, Dataset
from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._types.operation import (
    AsyncOperation, BaseOperation, Operation, ProtoOperation, ResultTypeT_co
)

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .model import BatchMetadataType, BatchResultType

logger = get_logger(__name__)


class BaseBatchOperation(BaseOperation[ResultTypeT_co]):
    _result_type: type[ResultTypeT_co]

    def __init__(
        self,
        *,
        sdk: BaseSDK,
        id: str,
        proto_result_type: type[BatchResultType],
        proto_metadata_type: type[BatchMetadataType],
        initial_operation: ProtoOperation,
    ):  # pylint: disable=redefined-builtin
        self._task_id: str = ''
        self._total_batches: int = 0
        self._completed_batches: int = 0

        super().__init__(
            sdk=sdk,
            id=id,
            result_type=self._result_type,
            proto_result_type=proto_result_type,
            proto_metadata_type=proto_metadata_type,
            transformer=self._result_transformer,
            service_name='ai-foundation-models',
            initial_operation=initial_operation,
        )

    # NB: I don't want to make parent operation class Generic[MetadataTypeT] just to
    # properly annotate this
    def _on_new_metadata(self, metadata) -> None:
        logger.log(TRACE, "updating task_id and progress from metadata %r", metadata)

        self._task_id = metadata.task_id
        self._total_batches = metadata.total_batches
        self._completed_batches = metadata.completed_batches

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def total_batches(self) -> int:
        return self._total_batches

    @property
    def completed_batches(self) -> int:
        return self._completed_batches

    async def _result_transformer(self, proto: BatchResultType, timeout: float) -> ResultTypeT_co:
        dataset_id = proto.result_dataset_id

        logger.log(TRACE, "Converting batch result proto object %r to SDK dataset object", proto)
        # pylint: disable=protected-access
        return await self._sdk.datasets._get(dataset_id, timeout=timeout)

    def __repr__(self) -> str:
        progress = 'unknown'
        if self._total_batches:
            progress = f'{self._completed_batches}/{self._total_batches}'
        return (
            f'{self.__class__.__name__}'
            '<'
            f'operation_id={self.id}'
            f', task_id={self._task_id}'
            f', progress={progress}'
            '>'
        )


class AsyncBatchOperation(BaseBatchOperation[AsyncDataset], AsyncOperation[AsyncDataset]):
    _result_type = AsyncDataset


class BatchOperation(BaseBatchOperation[Dataset], Operation[Dataset]):
    _result_type = Dataset


BatchOperationTypeT = TypeVar('BatchOperationTypeT', bound=BaseBatchOperation)
