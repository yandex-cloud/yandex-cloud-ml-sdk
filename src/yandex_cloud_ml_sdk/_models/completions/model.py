# pylint: disable=arguments-renamed,no-name-in-module,protected-access
from __future__ import annotations

import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, AsyncIterator, Generic, Iterator, Literal, cast

from google.protobuf.wrappers_pb2 import BoolValue
from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import CompletionOptions, ReasoningOptions
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Tool as ProtoCompletionsTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolChoice as ProtoToolChoice
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    BatchCompletionMetadata, BatchCompletionRequest, CompletionRequest, CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationAsyncServiceStub, TextGenerationBatchServiceStub, TextGenerationServiceStub, TokenizerServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall, ToolCall, ToolCallTypeT
from yandex_cloud_ml_sdk._tuning.tuning_task import AsyncTuningTask, TuningTask, TuningTaskTypeT
from yandex_cloud_ml_sdk._types.batch.domain import AsyncBatchSubdomain, BatchSubdomain, BatchSubdomainTypeT
from yandex_cloud_ml_sdk._types.batch.model import AsyncModelBatchMixin, BaseModelBatchMixin, ModelBatchMixin
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import (
    ModelAsyncMixin, ModelSyncMixin, ModelSyncStreamMixin, ModelTuneMixin, OperationTypeT
)
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._types.schemas import ResponseType, make_response_format_kwargs
from yandex_cloud_ml_sdk._types.tools.tool_choice import ToolChoiceType
from yandex_cloud_ml_sdk._types.tools.tool_choice import coerce_to_proto as coerce_to_proto_tool_choice
from yandex_cloud_ml_sdk._types.tuning.datasets import TuningDatasetsType
from yandex_cloud_ml_sdk._types.tuning.optimizers import BaseOptimizer
from yandex_cloud_ml_sdk._types.tuning.schedulers import BaseScheduler
from yandex_cloud_ml_sdk._types.tuning.tuning_types import BaseTuningType
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .config import CompletionTool, GPTModelConfig, ReasoningMode, ReasoningModeType
from .message import MessageInputType, messages_to_proto
from .result import GPTModelResult
from .token import Token
from .tune_params import GPTModelTuneParams

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._types.langchain import BaseYandexLanguageModel


class BaseGPTModel(
    Generic[OperationTypeT, TuningTaskTypeT, ToolCallTypeT, BatchSubdomainTypeT],
    ModelSyncMixin[GPTModelConfig, GPTModelResult[ToolCallTypeT]],
    ModelSyncStreamMixin[GPTModelConfig, GPTModelResult[ToolCallTypeT]],
    ModelAsyncMixin[GPTModelConfig, GPTModelResult[ToolCallTypeT], OperationTypeT],
    ModelTuneMixin[GPTModelConfig, GPTModelResult[ToolCallTypeT], GPTModelTuneParams, TuningTaskTypeT],
    BaseModelBatchMixin[GPTModelConfig, GPTModelResult[ToolCallTypeT], BatchSubdomainTypeT],
):
    """
    A class for GPT models providing various functionalities
    including tuning, and batch processing.
    """
    _config_type = GPTModelConfig
    _result_type: type[GPTModelResult[ToolCallTypeT]]
    _operation_type: type[OperationTypeT]
    _proto_result_type = CompletionResponse

    _tuning_params_type = GPTModelTuneParams
    _tuning_operation_type: type[TuningTaskTypeT]

    _batch_service_stub = TextGenerationBatchServiceStub
    _batch_proto_metadata_type = BatchCompletionMetadata

    def langchain(self, model_type: Literal["chat"] = "chat", timeout: int = 60) -> BaseYandexLanguageModel:
        """
        Initializes a langchain model based on the specified model type.

        :param model_type: the type of langchain model to initialize.
            Defaults to ``"chat"``.
        :param timeout: the timeout which sets the default for the langchain model object.
            Defaults to 60 seconds.
        """
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
        max_tokens: UndefinedOr[int] = UNDEFINED,
        reasoning_mode: UndefinedOr[ReasoningModeType] = UNDEFINED,
        response_format: UndefinedOr[ResponseType] = UNDEFINED,
        tools: UndefinedOr[Sequence[CompletionTool] | CompletionTool] = UNDEFINED,
        parallel_tool_calls: UndefinedOr[bool] = UNDEFINED,
        tool_choice: UndefinedOr[ToolChoiceType] = UNDEFINED,
    ) -> Self:
        """
        Configures the model with specified parameters.

        :param temperature: a sampling temperature to use - higher values mean more random results. Should be a double number between 0 (inclusive) and 1 (inclusive).
        :param max_tokens: a maximum number of tokens to generate in the response.
        :param reasoning_mode: the mode of reasoning to apply during generation, allowing the model to perform internal reasoning before responding.
            Read more about possible modes in the
            `reasoning documentation <https://yandex.cloud/docs/foundation-models/text-generation/api-ref/TextGeneration/completion#yandex.cloud.ai.foundation_models.v1.ReasoningOptions>`_.
        :param response_format: a format of the response returned by the model. Could be a JsonSchema, a JSON string, or a pydantic model.
            Read more about possible response formats in the
            `structured output documentation <https://yandex.cloud/docs/foundation-models/concepts/yandexgpt/#structured-output>`_.
        :param tools: tools to use for completion. Can be a sequence or a single tool.
        :param parallel_tool_calls: whether to allow parallel calls to tools during completion.
            Defaults to ``true``.
        :param tool_choice: the strategy for choosing tools.
            There are several ways to configure ``tool_choice`` for query processing:
            - no tools to call (tool_choice=``'none'``);
            - required to call any tool (tool_choice=``'required'``);
            - call a specific tool (tool_choice=``{'type': 'function', 'function': {'name': 'another_calculator'}}`` or directly passing a tool object).
        """
        return super().configure(
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_mode=reasoning_mode,
            response_format=response_format,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            tool_choice=tool_choice,
        )

    def _make_completion_options(self, *, stream: bool | None) -> CompletionOptions:
        completion_options_kwargs: dict[str, Any] = {}

        if stream is not None:
            completion_options_kwargs['stream'] = stream

        c = self._config

        if c.max_tokens is not None:
            completion_options_kwargs['max_tokens'] = {'value': c.max_tokens}
        if c.temperature is not None:
            completion_options_kwargs['temperature'] = {'value': c.temperature}
        if c.reasoning_mode is not None:
            reasoning_mode = ReasoningMode._coerce(c.reasoning_mode)._to_proto()
            reasoning_options = ReasoningOptions(mode=reasoning_mode)  # type: ignore[arg-type]
            completion_options_kwargs['reasoning_options'] = reasoning_options

        return CompletionOptions(**completion_options_kwargs)

    def _make_request(
        self,
        *,
        messages: MessageInputType,
        stream: bool | None,
    ) -> CompletionRequest:
        c = self._config

        response_format_kwargs = make_response_format_kwargs(c.response_format)

        tools: tuple[BaseTool, ...] = ()
        if c.tools is not None:
            tools = coerce_tuple(c.tools, BaseTool)  # type: ignore[type-abstract]

        parallel_tool_calls: None | BoolValue = None
        if c.parallel_tool_calls is not None:
            parallel_tool_calls = BoolValue(value=c.parallel_tool_calls)

        tool_choice: None | ProtoToolChoice = None
        if c.tool_choice is not None:
            tool_choice = coerce_to_proto_tool_choice(c.tool_choice, expected_type=ProtoToolChoice)

        return CompletionRequest(
            model_uri=self._uri,
            completion_options=self._make_completion_options(stream=stream),
            messages=messages_to_proto(messages),
            tools=[tool._to_proto(ProtoCompletionsTool) for tool in tools],
            parallel_tool_calls=parallel_tool_calls,
            tool_choice=tool_choice,
            **response_format_kwargs,
        )

    def _make_batch_request(self, dataset_id: str) -> BatchCompletionRequest:
        for field in ('tools', 'tool_choice', 'parallel_tool_calls'):
            value = getattr(self.config, field)
            if value is not None:
                warnings.warn(
                    f"The GPTModel.config.{field} is configured, "
                    "but it is not supported in the batch run, so it will be ignored.",
                    UserWarning, 4
                )

        response_format_kwargs = make_response_format_kwargs(self._config.response_format)

        return BatchCompletionRequest(
            model_uri=self.uri,
            completion_options=self._make_completion_options(stream=False),
            source_dataset_id=dataset_id,
            **response_format_kwargs,
        )

    async def _run_sync_impl(
        self,
        *,
        messages: MessageInputType,
        stream: bool,
        timeout: int,
    ) -> AsyncIterator[GPTModelResult[ToolCallTypeT]]:
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
                yield self._result_type._from_proto(proto=response, sdk=self._sdk)

        # something like mypy or pylint asking me to put this return here
        return

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        messages: MessageInputType,
        *,
        timeout=180,
    ) -> GPTModelResult[ToolCallTypeT]:
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
        timeout=180,
    ) -> AsyncIterator[GPTModelResult[ToolCallTypeT]]:
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

@doc_from(BaseGPTModel)
class AsyncGPTModel(
    BaseGPTModel[
        AsyncOperation[GPTModelResult[AsyncToolCall]],
        AsyncTuningTask['AsyncGPTModel'],
        AsyncToolCall,
        AsyncBatchSubdomain,
    ],
    AsyncModelBatchMixin,
):
    _operation_type = AsyncOperation[GPTModelResult[AsyncToolCall]]
    _tune_operation_type = AsyncTuningTask['AsyncGPTModel']
    _result_type = GPTModelResult[AsyncToolCall]

    async def run(
        self,
        messages: MessageInputType,
        *,
        timeout=180,
    ) -> GPTModelResult[AsyncToolCall]:
        """
        Executes the model with the provided messages.

        :param messages: the input messages to process. Could be a string, a dictionary, or a result object.
            Read more about other possible message types in the
            `corresponding documentation <https://yandex.cloud/docs/foundation-models/sdk/#usage>`_.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._run(
            messages=messages,
            timeout=timeout
        )

    async def run_stream(
        self,
        messages: MessageInputType,
        *,
        timeout=180,
    ) -> AsyncIterator[GPTModelResult[AsyncToolCall]]:
        """
        Executes the model with the provided messages
        and yields partial results as they become available.

        :param messages: the input messages to process.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
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
    ) -> AsyncOperation[GPTModelResult[AsyncToolCall]]:
        """
        Initiates a deferred execution of the model with the provided messages.

        :param messages: the input messages to process.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._run_deferred(
            messages=messages,
            timeout=timeout,
        )

    async def attach_deferred(self, operation_id: str, timeout: float = 60) -> AsyncOperation[GPTModelResult[AsyncToolCall]]:
        """
        Attaches to an ongoing deferred operation using its operation id.

        :param operation_id: the id of the deferred operation to attach to.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._attach_deferred(operation_id=operation_id, timeout=timeout)

    async def tokenize(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> tuple[Token, ...]:
        """
        Tokenizes the provided messages into a tuple of tokens.

        :param messages: the input messages to tokenize.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
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
        """Initiate a deferred tuning process for the model.

        :param train_datasets: the dataset objects and/or dataset ids used for training of the model.
        :param validation_datasets: the dataset objects and/or dataset ids used for validation of the model.
        :param name: the name of the tuning task.
        :param description: the description of the tuning task.
        :param labels: labels for the tuning task.
        :param seed: a random seed for reproducibility.
        :param lr: a learning rate for tuning.
        :param n_samples: a number of samples for tuning.
        :param additional_arguments: additional arguments for tuning.
        :param tuning_type: a type of tuning to be applied.
        :param scheduler: a scheduler for tuning.
        :param optimizer: an optimizer for tuning.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
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
        """Tune the model with the specified training datasets and parameters.

        :param train_datasets: the dataset objects and/or dataset ids used for training of the model.
        :param validation_datasets: the dataset objects and/or dataset ids used for validation of the model.
        :param name: the name of the tuning task.
        :param description: the description of the tuning task.
        :param labels: labels for the tuning task.
        :param seed: a random seed for reproducibility.
        :param lr: a learning rate for tuning.
        :param n_samples: a number of samples for tuning.
        :param additional_arguments: additional arguments for tuning.
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
        """Attach a deferred tuning task using its task id.

        :param task_id: the id of the deferred tuning task to attach to.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._attach_tune_deferred(task_id=task_id, timeout=timeout)

@doc_from(BaseGPTModel)
class GPTModel(
    BaseGPTModel[
        Operation[GPTModelResult[ToolCall]],
        TuningTask['GPTModel'],
        ToolCall,
        BatchSubdomain,
    ],
    ModelBatchMixin,
):
    _operation_type = Operation[GPTModelResult[ToolCall]]
    _tune_operation_type = TuningTask['GPTModel']
    _result_type = GPTModelResult[ToolCall]
    __run = run_sync(BaseGPTModel._run)
    __run_stream = run_sync_generator(BaseGPTModel._run_stream)
    __run_deferred = run_sync(BaseGPTModel._run_deferred)
    __attach_deferred = run_sync(BaseGPTModel._attach_deferred)
    __tokenize = run_sync(BaseGPTModel._tokenize)
    __tune_deferred = run_sync(BaseGPTModel._tune_deferred)
    __tune = run_sync(BaseGPTModel._tune)
    __attach_tune_deferred = run_sync(BaseGPTModel._attach_tune_deferred)

    @doc_from(AsyncGPTModel.run)
    def run(
        self,
        messages: MessageInputType,
        *,
        timeout=180,
    ) -> GPTModelResult[ToolCall]:
        return self.__run(
            messages=messages,
            timeout=timeout
        )

    @doc_from(AsyncGPTModel.run_stream)
    def run_stream(
        self,
        messages: MessageInputType,
        *,
        timeout=180,
    ) -> Iterator[GPTModelResult[ToolCall]]:
        yield from self.__run_stream(
            messages=messages,
            timeout=timeout
        )

    @doc_from(AsyncGPTModel.run_deferred)
    def run_deferred(
        self,
        messages: MessageInputType,
        *,
        timeout=60
    ) -> Operation[GPTModelResult[ToolCall]]:
        return self.__run_deferred(
            messages=messages,
            timeout=timeout,
        )

    @doc_from(AsyncGPTModel.attach_deferred)
    def attach_deferred(self, operation_id: str, timeout: float = 60) -> Operation[GPTModelResult[ToolCall]]:
        return cast(
            Operation[GPTModelResult[ToolCall]],
            self.__attach_deferred(operation_id=operation_id, timeout=timeout)
        )

    @doc_from(AsyncGPTModel.tokenize)
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
    @doc_from(AsyncGPTModel.tune_deferred)
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
    @doc_from(AsyncGPTModel.tune)
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

    @doc_from(AsyncGPTModel.attach_tune_deferred)
    def attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> TuningTask[GPTModel]:
        return cast(
            TuningTask[GPTModel],
            self.__attach_tune_deferred(task_id=task_id, timeout=timeout)
        )
