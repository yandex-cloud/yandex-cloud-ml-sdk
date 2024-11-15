# pylint: disable=arguments-renamed,no-name-in-module,protected-access
from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, Literal

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import CompletionOptions
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionRequest, CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationAsyncServiceStub, TextGenerationServiceStub, TokenizerServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelAsyncMixin, ModelSyncMixin, ModelSyncStreamMixin, OperationTypeT
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .config import GPTModelConfig
from .message import MessageInputType, messages_to_proto
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
                yield GPTModelResult._from_proto(response, sdk=self._sdk)

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


class AsyncGPTModel(BaseGPTModel[AsyncOperation[GPTModelResult]]):
    _operation_type = AsyncOperation

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


class GPTModel(BaseGPTModel[Operation[GPTModelResult]]):
    _operation_type = Operation
    __run = run_sync(BaseGPTModel._run)
    __run_stream = run_sync_generator(BaseGPTModel._run_stream)
    __run_deferred = run_sync(BaseGPTModel._run_deferred)
    __tokenize = run_sync(BaseGPTModel._tokenize)

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
