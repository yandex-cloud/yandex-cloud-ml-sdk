# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import Generic, TypeVar, cast

from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    DescribeTuningRequest, DescribeTuningResponse, GetOptionsRequest, GetOptionsResponse, TuningRequest
)
from yandex.cloud.ai.tuning.v1.tuning_service_pb2_grpc import TuningServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, coerce_path, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.model import ModelTuneMixin
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType, coerce_datasets
from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .tuning_task import AsyncTuningTask, TuningTask, TuningTaskTypeT


class BaseTuning(BaseDomain, Generic[TuningTaskTypeT]):
    _tuning_impl: type[TuningTaskTypeT]

    def _to_weighted_datasets(
        self,
        datasets: UndefinedOr[TuningDatasetsType]
    ) -> tuple[TuningRequest.WeightedDataset, ...]:
        defined = get_defined_value(datasets, None)
        if not defined:
            return ()

        coerced = coerce_datasets(defined)

        return tuple(
            TuningRequest.WeightedDataset(
                dataset_id=dataset_id,
                weight=weight
            ) for dataset_id, weight in coerced
        )

    async def _create_deferred(
        self,
        *,
        model_uri: str,
        result_type: type[ModelTuneMixin],
        train_datasets: TuningDatasetsType,
        validation_datasets: UndefinedOr[TuningDatasetsType],
        tuning_params: BaseTuningParams,
        name: UndefinedOr[str],
        description: UndefinedOr[str],
        labels: UndefinedOr[dict[str, str]],
        timeout: float,
    ) -> TuningTaskTypeT:
        tuning_argument_name = tuning_params._proto_tuning_argument_name

        request = TuningRequest(
            base_model_uri=model_uri,
            train_datasets=self._to_weighted_datasets(train_datasets),
            validation_datasets=self._to_weighted_datasets(validation_datasets),
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            **{tuning_argument_name: tuning_params.to_proto()}
        )
        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            response = await self._client.call_service(
                stub.Tune,
                request=request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        return self._tuning_impl(
            operation_id=response.id,
            task_id=None,
            sdk=self._sdk,
            result_type=result_type,
        )

    async def _get_task_result_type(
        self,
        task_id: str,
        *,
        timeout: float = 60,
    ) -> type[ModelTuneMixin]:
        request = GetOptionsRequest(task_id=task_id)

        async with self._client.get_service_stub(
            TuningServiceStub,
            timeout=timeout,
        ) as stub:
            response = await self._client.call_service(
                stub.GetOptions,
                request=request,
                timeout=timeout,
                expected_type=GetOptionsResponse,
            )

        class_map = self._sdk.models._tuning_map
        for tuning_params_name, model_class in class_map.items():
            options = getattr(response, tuning_params_name)
            if options:
                return model_class

        raise RuntimeError(
            "task have a task params, different from supported types: {list(maps.keys())}; "
            "please, update SDK"
        )

    async def _get(
        self,
        task_id: str,
        *,
        timeout: float = 60,
    ) -> TuningTaskTypeT:
        result_type = await self._get_task_result_type(
            task_id=task_id,
            timeout=timeout
        )

        return self._tuning_impl(
            operation_id=None,
            task_id=task_id,
            sdk=self._sdk,
            result_type=result_type,
        )

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[TuningTaskTypeT]:
        pass


class AsyncTuning(BaseTuning[AsyncTuningTask]):
    _tuning_impl = AsyncTuningTask

    async def get(
        self,
        task_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncTuningTask:
        return await self._get(task_id=task_id, timeout=timeout)


class Tuning(BaseTuning[TuningTask]):
    _tuning_impl = TuningTask
