from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset, Dataset
from yandex_cloud_ml_sdk._logging import TRACE, get_logger
from yandex_cloud_ml_sdk._types.operation import (
    AsyncOperationMixin, OperationInterface, OperationStatus, ResultTypeT_co, SyncOperationMixin
)

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    from .model import BatchResultType

logger = get_logger(__name__)


class BaseBatchTask(OperationInterface[ResultTypeT_co, OperationStatus]):
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
        self._completed_batches: int = 0
        self._total_batches: int = 0

    @property
    def task_id(self) -> str:
        return self._id

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
        return (
            f'{self.__class__.__name__}'
            f'<{self._id}>'
        )


class AsyncBatchTask(AsyncOperationMixin[AsyncDataset, OperationStatus], BaseBatchTask[AsyncDataset]):
    _result_type = AsyncDataset


class BatchTask(SyncOperationMixin[Dataset, OperationStatus], BaseBatchTask[Dataset]):
    _result_type = Dataset


BatchTaskTypeT = TypeVar('BatchTaskTypeT', bound=BaseBatchTask)
