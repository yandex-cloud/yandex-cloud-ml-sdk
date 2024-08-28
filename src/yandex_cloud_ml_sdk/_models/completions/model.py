# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Iterable, Literal

from typing_extensions import override
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import CompletionOptions
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionRequest, CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationAsyncServiceStub, TextGenerationServiceStub, TokenizerServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.model import ModelAsyncMixin, ModelSyncMixin, ModelSyncStreamMixin, OperationTypeT
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .config import GPTModelConfig
from .message import MessageType, messages_to_proto
from .result import GPTModelResult
from .token import Token

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._types.langchain import BaseYandexLanguageModel


class BaseGPTModel(
    ModelSyncMixin[GPTModelConfig, GPTModelResult],
    ModelSyncStreamMixin[GPTModelConfig, GPTModelResult],
    ModelAsyncMixin[GPTModelConfig, GPTModelResult, OperationTypeT],
):
    _config_type = GPTModelConfig
    _result_type = GPTModelResult
    _operation_type: type[OperationTypeT]

    def langchain(self, model_type: Literal["chat"] = "chat", timeout: int = 60) -> BaseYandexLanguageModel:
        from .langchain import ChatYandexGPT  # pylint: disable=import-outside-toplevel

        if model_type == "chat":
        # idk why but pylint thinks this class still abstract
            return ChatYandexGPT(ycmlsdk_model=self, timeout=timeout)  # pylint: disable=abstract-class-instantiated

        raise ValueError(f"unknown langchain model {type=}")

    def _make_request(
        self,
        *,
        messages: MessageType | Iterable[MessageType],
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
        messages: MessageType | Iterable[MessageType],
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
                yield GPTModelResult._from_proto(response)

        # something like mypy or pylint asking me to put this return here
        return

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        messages: MessageType | Iterable[MessageType],
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
        messages: MessageType | Iterable[MessageType],
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
        messages: MessageType | Iterable[MessageType],
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
            )

    @override
    def attach_async(self, operation_id: str) -> OperationTypeT:
        return self._operation_type(
            id=operation_id,
            sdk=self._sdk,
            result_type=self._result_type,
        )

    async def _tokenize(
        self,
        messages: MessageType | Iterable[MessageType],
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


class AsyncGPTModel(BaseGPTModel):
    run = BaseGPTModel._run
    run_stream = BaseGPTModel._run_stream
    run_deferred = BaseGPTModel._run_deferred
    tokenize = BaseGPTModel._tokenize
    _operation_type = AsyncOperation


class GPTModel(BaseGPTModel):
    run = run_sync(BaseGPTModel._run)
    run_stream = run_sync_generator(BaseGPTModel._run_stream)
    run_deferred = run_sync(BaseGPTModel._run_deferred)
    tokenize = run_sync(BaseGPTModel._tokenize)
    _operation_type = Operation
