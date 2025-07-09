# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2 import (
    TextEmbeddingRequest, TextEmbeddingResponse
)
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2_grpc import EmbeddingsServiceStub

from yandex_cloud_ml_sdk._tuning.tuning_task import AsyncTuningTask, TuningTask, TuningTaskTypeT
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin, ModelTuneMixin
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType
from yandex_cloud_ml_sdk._types.tuning.optimizers import BaseOptimizer
from yandex_cloud_ml_sdk._types.tuning.schedulers import BaseScheduler
from yandex_cloud_ml_sdk._types.tuning.tuning_types import BaseTuningType
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import TextEmbeddingsModelConfig
from .result import TextEmbeddingsModelResult
from .tune_params import EmbeddingsTuneType, TextEmbeddingsModelTuneParams


class BaseTextEmbeddingsModel(
    ModelSyncMixin[TextEmbeddingsModelConfig, TextEmbeddingsModelResult],
    ModelTuneMixin[
        TextEmbeddingsModelConfig,
        TextEmbeddingsModelResult,
        TextEmbeddingsModelTuneParams,
        TuningTaskTypeT
    ],
):
    """
    A class for text embeddings models, providing configuration,
    request creation, and execution functionalities.
    """
    _config_type = TextEmbeddingsModelConfig
    _result_type = TextEmbeddingsModelResult
    _tuning_params_type = TextEmbeddingsModelTuneParams
    _tuning_operation_type: type[TuningTaskTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
    ) -> Self:
        """
        This method calls the parent class's configure method and
        returns the configured model instance.
        """
        return super().configure()

    def _make_request(
        self,
        *,
        text: str,
    ) -> TextEmbeddingRequest:
        return TextEmbeddingRequest(
            model_uri=self._uri,
            text=text,
        )

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        request = self._make_request(
            text=text,
        )
        async with self._client.get_service_stub(EmbeddingsServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.TextEmbedding,
                request,
                timeout=timeout,
                expected_type=TextEmbeddingResponse,
            )
            return TextEmbeddingsModelResult._from_proto(proto=response, sdk=self._sdk)

@doc_from(BaseTextEmbeddingsModel)
class AsyncTextEmbeddingsModel(BaseTextEmbeddingsModel):
    _tune_operation_type = AsyncTuningTask

    async def run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        """Run the model to generate text embeddings.

        :param text: the input text for which embeddings are to be generated.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._run(
            text=text,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    async def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
        embeddings_tune_type: EmbeddingsTuneType,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        dimensions: UndefinedOr[Sequence[int]] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncTuningTask['AsyncTextEmbeddingsModel']:
        """Initiate a deferred tuning process for the model.

        :param train_datasets: the dataset objects and/or dataset ids used for training of the model.
        :param embeddings_tune_type: the type of tuning to be applied (e.g. pair or triplet).
        :param validation_datasets: the dataset objects and/or dataset ids used for validation of the model.
        :param name: the name of the tuning task.
        :param description: the description of the tuning task.
        :param labels: labels for the tuning task.
        :param seed: a random seed for reproducibility.
        :param lr: a learning rate for tuning.
        :param n_samples: a number of samples for tuning.
        :param additional_arguments: additional arguments for tuning.
        :param dimensions: dimensions for the embeddings.
        :param tuning_type: a type of tuning to be applied.
        :param scheduler: a scheduler for tuning.
        :param optimizer: an optimizer for tuning.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            embeddings_tune_type=embeddings_tune_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            dimensions=dimensions,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
        )

    # pylint: disable=too-many-locals
    async def tune(
        self,
        train_datasets: TuningDatasetsType,
        *,
        embeddings_tune_type: EmbeddingsTuneType,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        dimensions: UndefinedOr[Sequence[int]] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 60,
    ) -> Self:
        """Tune the model with the specified training datasets and parameters.

        :param train_datasets: the dataset objects and/or dataset ids used for training of the model.
        :param embeddings_tune_type: the type of tuning to be applied (e.g. pair or triplet).
        :param validation_datasets: the dataset objects and/or dataset ids used for validation of the model.
        :param name: the name of the tuning task.
        :param description: the description of the tuning task.
        :param labels: labels for the tuning task.
        :param seed: a random seed for reproducibility.
        :param lr: a learning rate for tuning.
        :param n_samples: a number of samples for tuning.
        :param additional_arguments: additional arguments for tuning.
        :param dimensions: dimensions for the embeddings.
        :param tuning_type: a type of tuning to be applied.
        :param scheduler: a scheduler for tuning.
        :param optimizer: an optimizer for tuning.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        :param poll_timeout: the maximum time to wait while polling for completion of the tuning task.
            Defaults to 259200 seconds (72 hours).
        :param poll_interval: the interval between polling attempts during the tuning process.
            Defaults to 60 seconds.
        """
        return await self._tune(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            embeddings_tune_type=embeddings_tune_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            dimensions=dimensions,
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
    ) -> AsyncTuningTask['AsyncTextEmbeddingsModel']:
        """Attach a deferred tuning task using its task ID.

        :param task_id: the ID of the deferred tuning task to attach to.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._attach_tune_deferred(task_id=task_id, timeout=timeout)


@doc_from(BaseTextEmbeddingsModel)
class TextEmbeddingsModel(BaseTextEmbeddingsModel):
    _tune_operation_type = TuningTask
    __run = run_sync(BaseTextEmbeddingsModel._run)
    __tune_deferred = run_sync(BaseTextEmbeddingsModel._tune_deferred)
    __tune = run_sync(BaseTextEmbeddingsModel._tune)
    __attach_tune_deferred = run_sync(BaseTextEmbeddingsModel._attach_tune_deferred)

    @doc_from(AsyncTextEmbeddingsModel.run)
    def run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        return self.__run(
            text=text,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    @doc_from(AsyncTextEmbeddingsModel.tune_deferred)
    def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
        embeddings_tune_type: EmbeddingsTuneType,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        dimensions: UndefinedOr[Sequence[int]] = UNDEFINED,
        tuning_type: UndefinedOr[BaseTuningType] = UNDEFINED,
        scheduler: UndefinedOr[BaseScheduler] = UNDEFINED,
        optimizer: UndefinedOr[BaseOptimizer] = UNDEFINED,
        timeout: float = 60,
    ) -> TuningTask[TextEmbeddingsModel]:
        result = self.__tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            embeddings_tune_type=embeddings_tune_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            dimensions=dimensions,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
        )
        return cast(TuningTask[TextEmbeddingsModel], result)

    # pylint: disable=too-many-locals
    @doc_from(AsyncTextEmbeddingsModel.tune)
    def tune(
        self,
        train_datasets: TuningDatasetsType,
        *,
        embeddings_tune_type: EmbeddingsTuneType,
        validation_datasets: UndefinedOr[TuningDatasetsType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        seed: UndefinedOr[int] = UNDEFINED,
        lr: UndefinedOr[float] = UNDEFINED,
        n_samples: UndefinedOr[int] = UNDEFINED,
        additional_arguments: UndefinedOr[str] = UNDEFINED,
        dimensions: UndefinedOr[Sequence[int]] = UNDEFINED,
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
            embeddings_tune_type=embeddings_tune_type,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout,
            seed=seed,
            lr=lr,
            n_samples=n_samples,
            additional_arguments=additional_arguments,
            dimensions=dimensions,
            tuning_type=tuning_type,
            scheduler=scheduler,
            optimizer=optimizer,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    @doc_from(AsyncTextEmbeddingsModel.attach_tune_deferred)
    def attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> TuningTask[TextEmbeddingsModel]:
        return cast(
            TuningTask[TextEmbeddingsModel],
            self.__attach_tune_deferred(task_id=task_id, timeout=timeout)
        )
