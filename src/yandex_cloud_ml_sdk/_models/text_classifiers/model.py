# pylint: disable=arguments-renamed,no-name-in-module,protected-access
from __future__ import annotations

from dataclasses import astuple
from typing import Sequence, cast

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_pb2 import (
    ClassificationSample as TextClassificationSampleProto
)
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2 import (
    FewShotTextClassificationRequest, FewShotTextClassificationResponse, TextClassificationRequest,
    TextClassificationResponse
)
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2_grpc import (
    TextClassificationServiceStub
)

from yandex_cloud_ml_sdk._tuning.tuning_task import AsyncTuningTask, TuningTask, TuningTaskTypeT
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin, ModelTuneMixin
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType
from yandex_cloud_ml_sdk._types.tuning.optimizers import BaseOptimizer
from yandex_cloud_ml_sdk._types.tuning.schedulers import BaseScheduler
from yandex_cloud_ml_sdk._types.tuning.tuning_types import BaseTuningType
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import TextClassifiersModelConfig
from .result import FewShotTextClassifiersModelResult, TextClassifiersModelResult, TextClassifiersModelResultBase
from .tune_params import ClassificationTuningTypes, TextClassifiersModelTuneParams
from .types import TextClassificationSample


class BaseTextClassifiersModel(
    ModelSyncMixin[TextClassifiersModelConfig, TextClassifiersModelResultBase],
    ModelTuneMixin[
        TextClassifiersModelConfig,
        TextClassifiersModelResult,
        TextClassifiersModelTuneParams,
        TuningTaskTypeT
    ],
):
    _config_type = TextClassifiersModelConfig
    _result_type = TextClassifiersModelResultBase
    _tuning_params_type = TextClassifiersModelTuneParams
    _tuning_operation_type: type[TuningTaskTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        task_description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[Sequence[str]] = UNDEFINED,
        samples: UndefinedOr[Sequence[TextClassificationSample]] = UNDEFINED,
    ) -> Self:
        return super().configure(
            task_description=task_description,
            labels=labels,
            samples=samples,
        )

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        if any(v is not None for v in astuple(self._config)):
            return await self._run_few_shot(text, timeout=timeout)

        return await self._run_classify(text, timeout=timeout)

    async def _run_classify(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResult:
        request = TextClassificationRequest(
            model_uri=self._uri,
            text=text,
        )
        async with self._client.get_service_stub(TextClassificationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Classify,
                request,
                timeout=timeout,
                expected_type=TextClassificationResponse,
            )
            return TextClassifiersModelResult._from_proto(proto=response, sdk=self._sdk)

    async def _run_few_shot(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> FewShotTextClassifiersModelResult:
        config = self._config

        if config.labels is None or config.task_description is None:
            raise ValueError(
                "Incorrect combination of config values. Use one of the three following combinations:\n",
                " * The `labels`, `task_description` and `samples` parameters must have specific values.\n"
                " * The `labels` and `task_description` parameters must"
                " have specific values while `samples` has the None value.\n"
                " * All three parameters — `labels', `task_description` and `samples` —"
                " must take the None value simultaneously."
            )

        samples = config.samples or []
        proto_samples = [
            TextClassificationSampleProto(
                text=sample['text'],
                label=sample['label'],
            ) for sample in samples
        ]
        request = FewShotTextClassificationRequest(
            model_uri=self._uri,
            text=text,
            task_description=config.task_description,
            labels=list(config.labels),
            samples=(proto_samples if proto_samples else None),
        )

        async with self._client.get_service_stub(TextClassificationServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.FewShotClassify,
                request,
                timeout=timeout,
                expected_type=FewShotTextClassificationResponse,
            )
            return FewShotTextClassifiersModelResult._from_proto(proto=response, sdk=self._sdk)


class AsyncTextClassifiersModel(BaseTextClassifiersModel[AsyncTuningTask['AsyncTextClassifiersModel']]):
    _tune_operation_type = AsyncTuningTask

    async def run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        return await self._run(
            text=text,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    async def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
        classification_type: ClassificationTuningTypes,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncTuningTask['AsyncTextClassifiersModel']:
        return await self._tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            classification_type=classification_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
        )

    # pylint: disable=too-many-locals
    async def tune(
        self,
        train_datasets: TuningDatasetsType,
        *,
        classification_type: ClassificationTuningTypes,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 60,
    ) -> Self:
        return await self._tune(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            classification_type=classification_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    async def attach_tune_deferred(
        self,
        task_id: str,
        *,
        timeout: float = 60
    ) -> AsyncTuningTask['AsyncTextClassifiersModel']:
        return await self._attach_tune_deferred(task_id=task_id, timeout=timeout)


class TextClassifiersModel(BaseTextClassifiersModel[TuningTask['TextClassifiersModel']]):
    _tune_operation_type = TuningTask
    __run = run_sync(BaseTextClassifiersModel._run)
    __tune_deferred = run_sync(BaseTextClassifiersModel._tune_deferred)
    __tune = run_sync(BaseTextClassifiersModel._tune)
    __attach_tune_deferred = run_sync(BaseTextClassifiersModel._attach_tune_deferred)

    def run(
        self,
        text: str,
        *,
        timeout: float = 60,
    ) -> TextClassifiersModelResultBase:
        return self.__run(
            text=text,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
        classification_type: ClassificationTuningTypes,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
    ) -> TuningTask[TextClassifiersModel]:
        result = self.__tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            classification_type=classification_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
        )
        return cast(TuningTask[TextClassifiersModel], result)

    # pylint: disable=too-many-locals
    def tune(
        self,
        train_datasets: TuningDatasetsType,
        *,
        classification_type: ClassificationTuningTypes,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 60,
    ) -> Self:
        return self.__tune(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            classification_type=classification_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> TuningTask[TextClassifiersModel]:
        return cast(
            TuningTask[TextClassifiersModel],
            self.__attach_tune_deferred(task_id=task_id, timeout=timeout)
        )
