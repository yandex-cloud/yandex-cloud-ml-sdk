# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator, TypeVar

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, coerce_path, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType, coerce_datasets
from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

TuningTaskTypeT = TypeVar('TuningTaskTypeT')
TuningTask = None
AsyncTuningTask = None



class BaseTuning(BaseDomain, Generic[TuningTaskTypeT]):
    _tuning_impl: type[TuningTaskTypeT]

    async def _create_deferred(
        self,
        *,
        train_datasets: TuningDatasetsType,
        validation_datasets: UndefinedOr[TuningDatasetsType],
        model_uri: str,
        tuning_params: BaseTuningParams,
        name: UndefinedOr[str],
        description: UndefinedOr[str],
        labels: UndefinedOr[dict[str, str]],
        timeout: float,
    ) -> TuningTaskTypeT:

        return self._tuning_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get(
        self,
        tuning_id: str,
        *,
        timeout: float = 60,
    ) -> TuningTaskTypeT:

        return self._tuning_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[TuningTaskTypeT]:
        pass


class AsyncTuning(BaseTuning[AsyncTuningTask]):
    _tuning_impl = AsyncTuningTask


class Tuning(BaseTuning[TuningTask]):
    _tuning_impl = TuningTask
