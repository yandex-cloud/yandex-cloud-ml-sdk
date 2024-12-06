# pylint: disable=arguments-renamed,no-name-in-module,protected-access
from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Generic, Iterator, Literal, cast

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import CompletionOptions
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionRequest, CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationAsyncServiceStub, TextGenerationServiceStub, TokenizerServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._tuning.tuning_task import AsyncTuningTask, TuningTask, TuningTaskTypeT
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import (
    ModelAsyncMixin, ModelSyncMixin, ModelSyncStreamMixin, ModelTuneMixin, OperationTypeT
)
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType
from yandex_cloud_ml_sdk._types.tuning.optimizers import BaseOptimizer
from yandex_cloud_ml_sdk._types.tuning.schedulers import BaseScheduler
from yandex_cloud_ml_sdk._types.tuning.tuning_types import BaseTuningType
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .config import GPTModelConfig
from .message import MessageInputType, messages_to_proto
from .result import GPTModelResult
from .token import Token
from .tune_params import GPTModelTuneParams

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._types.langchain import BaseYandexLanguageModel


class BaseGPTModel(
    Generic[OperationTypeT, TuningTaskTypeT],
    ModelSyncMixin[GPTModelConfig, GPTModelResult],
    ModelSyncStreamMixin[GPTModelConfig, GPTModelResult],
    ModelAsyncMixin[GPTModelConfig, GPTModelResult, OperationTypeT],
    ModelTuneMixin[GPTModelConfig, GPTModelResult, GPTModelTuneParams, TuningTaskTypeT],
):
    _config_type = GPTModelConfig
    _result_type = GPTModelResult
    _operation_type: type[OperationTypeT]
    _proto_result_type = CompletionResponse

    _tuning_params_type = GPTModelTuneParams
    _tuning_operation_type: type[TuningTaskTypeT]

    def langchain(self, model_type: Literal["chat"] = "chat", timeout: int = 60) -> BaseYandexLanguageModel:
        from .langchain import ChatYandexGPT  # pylint: disable=import-outside-toplevel

        if model_type == "chat":
        # idk why but pylint thinks this class still abstract
            return ChatYandexGPT(ycmlsdk_model=self, timeout=timeout)  # pylint: disable=abstract-class-instantiated

        raise ValueError(f"unknown langchain model {type=}")

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        temperature: UndefinedOr[float] = UNDEFINED,
        max_tokens: UndefinedOr[int] = UNDEFINED
    ) -> Self:
        return super().configure(
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _make_request(
        self,
        *,
        messages: MessageInputType,
        stream: bool | None,
    ) -> CompletionRequest:
        completion_options_kwargs: dict[str, Any] = {}

        if stream is not None:
            completion_options_kwargs['stream'] = stream

        if self._config.max_tokens is not None:
            completion_options_kwargs['max_tokens'] = {'value': self._config.max_tokens}
        if self._config.temperature is not None:
            completion_options_kwargs['temperature'] = {'value': self._config.temperature}

        return CompletionRequest(
            model_uri=self._uri,
            completion_options=CompletionOptions(**completion_options_kwargs),
            messages=messages_to_proto(messages),
        )

    async def _run_sync_impl(
        self,
        *,
        messages: MessageInputType,
        stream: bool,
        timeout: int,
    ) -> AsyncIterator[GPTModelResult]:
        request = self._make_request(
            messages=messages,
            stream=stream,
        )
        async with self._client.get_service_stub(TextGenerationServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.Completion,
                request,
                timeout=timeout,
                expected_type=CompletionResponse,
            ):
                yield GPTModelResult._from_proto(proto=response, sdk=self._sdk)

        # something like mypy or pylint asking me to put this return here
        return

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> GPTModelResult:
        async for result in self._run_sync_impl(
            messages=messages,
            timeout=timeout,
            stream=False
        ):
            return result

        raise RuntimeError("call returned less then one result")

    @override
    # pylint: disable-next=arguments-differ
    async def _run_stream(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> AsyncIterator[GPTModelResult]:
        async for result in self._run_sync_impl(
            messages=messages,
            timeout=timeout,
            stream=True
        ):
            yield result

        return

    @override
    # pylint: disable-next=arguments-differ
    async def _run_deferred(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> OperationTypeT:
        request = self._make_request(
            messages=messages,
            stream=None,
        )
        async with self._client.get_service_stub(TextGenerationAsyncServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Completion,
                request,
                timeout=timeout,
                expected_type=ProtoOperation
            )
            return self._operation_type(
                id=response.id,
                sdk=self._sdk,
                result_type=self._result_type,
                proto_result_type=self._proto_result_type,
            )

    async def _tokenize(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> tuple[Token, ...]:
        request = self._make_request(
            messages=messages,
            stream=False,
        )
        async with self._client.get_service_stub(TokenizerServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.TokenizeCompletion,
                request,
                timeout=timeout,
                expected_type=TokenizeResponse
            )
            return tuple(Token._from_proto(t) for t in response.tokens)


class AsyncGPTModel(BaseGPTModel[AsyncOperation[GPTModelResult], AsyncTuningTask['AsyncGPTModel']]):
    _operation_type = AsyncOperation
    _tune_operation_type = AsyncTuningTask

    async def run(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> GPTModelResult:
        return await self._run(
            messages=messages,
            timeout=timeout
        )

    async def run_stream(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> AsyncIterator[GPTModelResult]:
        async for result in self._run_stream(
            messages=messages,
            timeout=timeout
        ):
            yield result

    async def run_deferred(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> AsyncOperation[GPTModelResult]:
        return await self._run_deferred(
            messages=messages,
            timeout=timeout,
        )

    async def attach_deferred(self, operation_id: str, timeout: float = 60) -> AsyncOperation[GPTModelResult]:
        return await self._attach_deferred(operation_id=operation_id, timeout=timeout)

    async def tokenize(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> tuple[Token, ...]:
        return await self._tokenize(
            messages=messages,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    async def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
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
    ) -> AsyncTuningTask['AsyncGPTModel']:
        return await self._tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
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

    async def attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> AsyncTuningTask['AsyncGPTModel']:
        return await self._attach_tune_deferred(task_id=task_id, timeout=timeout)


class GPTModel(BaseGPTModel[Operation[GPTModelResult], TuningTask['GPTModel']]):
    _operation_type = Operation
    _tune_operation_type = TuningTask
    __run = run_sync(BaseGPTModel._run)
    __run_stream = run_sync_generator(BaseGPTModel._run_stream)
    __run_deferred = run_sync(BaseGPTModel._run_deferred)
    __attach_deferred = run_sync(BaseGPTModel._attach_deferred)
    __tokenize = run_sync(BaseGPTModel._tokenize)
    __tune_deferred = run_sync(BaseGPTModel._tune_deferred)
    __tune = run_sync(BaseGPTModel._tune)
    __attach_tune_deferred = run_sync(BaseGPTModel._attach_tune_deferred)

    def run(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> GPTModelResult:
        return self.__run(
            messages=messages,
            timeout=timeout
        )

    def run_stream(
        self,
        messages: MessageInputType,
        *,
        timeout=60,
    ) -> Iterator[GPTModelResult]:
        yield from self.__run_stream(
            messages=messages,
            timeout=timeout
        )

    def run_deferred(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> Operation[GPTModelResult]:
        return self.__run_deferred(
            messages=messages,
            timeout=timeout,
        )

    def attach_deferred(self, operation_id: str, timeout: float = 60) -> Operation[GPTModelResult]:
        return cast(
            Operation[GPTModelResult],
            self.__attach_deferred(operation_id=operation_id, timeout=timeout)
        )

    def tokenize(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> tuple[Token, ...]:
        return self.__tokenize(
            messages=messages,
            timeout=timeout
        )

    # pylint: disable=too-many-locals
    def tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        *,
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
    ) -> TuningTask[GPTModel]:
        result = self.__tune_deferred(
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
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
        return cast(TuningTask[GPTModel], result)

    # pylint: disable=too-many-locals
    def tune(
        self,
        train_datasets: TuningDatasetsType,
        *,
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

    def attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> TuningTask[GPTModel]:
        return cast(
            TuningTask[GPTModel],
            self.__attach_tune_deferred(task_id=task_id, timeout=timeout)
        )
