from __future__ import annotations

from dataclasses import asdict
from typing import Any, AsyncIterator, Iterator, TypeVar

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from yandex_cloud_ml_sdk._types.langchain import BaseYandexLanguageModel
from yandex_cloud_ml_sdk._utils.langchain import make_async_run_manager
from yandex_cloud_ml_sdk._utils.sync import run_sync_generator_impl, run_sync_impl

from .message import TextMessageDict
from .model import BaseGPTModel  # pylint: disable=cyclic-import
from .result import Alternative, AlternativeStatus, GPTModelResult

GenerationClassT = TypeVar('GenerationClassT', bound=ChatGeneration)


def _transform_messages(history: list[BaseMessage]) -> list[TextMessageDict]:
    """Parse a sequence of messages into history.

    Returns:
        A list of parsed messages.
    """
    chat_history = []
    for message in history:
        text = message.content
        if not isinstance(text, str):
            raise TypeError('message content must be a string')

        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            # TODO: add warning log here
            continue

        chat_history.append(TextMessageDict({
            "text": text,
            "role": role,
        }))

    return chat_history


class ChatYandexGPT(BaseYandexLanguageModel[BaseGPTModel], BaseChatModel):
    class Config:
        arbitrary_types_allowed = True

    @property
    def _sdk(self):
        return self.ycmlsdk_model._sdk

    def _make_generation(
        self,
        result: GPTModelResult,
        alternative: Alternative,
        message_class: type[BaseMessage],
        generation_class: type[GenerationClassT],
        text_override: str | None = None
    ) -> GenerationClassT:
        sdk_usage = result.usage
        usage_metadata = UsageMetadata(
            input_tokens=sdk_usage.input_text_tokens,
            output_tokens=sdk_usage.completion_tokens,
            total_tokens=sdk_usage.total_tokens,
        )
        message = message_class(
            content=text_override or alternative.text,
            usage_metadata=usage_metadata
        )

        generation_info = {
            "status": alternative.status.name,
            "model_version": result.model_version,
        }

        return generation_class(
            message=message,
            generation_info=generation_info
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        async_run_manager = make_async_run_manager(run_manager) if run_manager else None
        coro = self._agenerate(
            messages=messages,
            stop=stop,
            run_manager=async_run_manager,
            **kwargs
        )
        return run_sync_impl(coro, self._sdk)

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        sdk_messages = _transform_messages(messages)
        sdk_result = await self.ycmlsdk_model._run(  # pylint: disable=protected-access
            messages=sdk_messages,
            timeout=self.timeout
        )

        generations = [
            self._make_generation(
                result=sdk_result,
                alternative=alternative,
                message_class=AIMessage,
                generation_class=ChatGeneration
            ) for alternative in sdk_result.alternatives
        ]

        return ChatResult(
            generations=generations,
            llm_output={
                "usage": asdict(sdk_result.usage),
                "model_version": sdk_result.model_version,
            }
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        async_run_manager = make_async_run_manager(run_manager) if run_manager else None
        async_iterator = self._astream(
            messages=messages,
            stop=stop,
            run_manager=async_run_manager,
            **kwargs
        )
        return run_sync_generator_impl(async_iterator, self._sdk)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        sdk_messages = _transform_messages(messages)

        current_text = ""
        async for sdk_result in self.ycmlsdk_model._run_stream(  # pylint: disable=protected-access
            messages=sdk_messages,
            timeout=self.timeout,
        ):
            alternative = sdk_result.alternatives[0]
            text = alternative.text
            if alternative.status == AlternativeStatus.CONTENT_FILTER:
                delta = text
            else:
                delta = text[len(current_text):]
                current_text = text

            generation = self._make_generation(
                sdk_result,
                alternative=alternative,
                message_class=AIMessageChunk,
                generation_class=ChatGenerationChunk,
                text_override=delta,
            )
            yield generation


ChatYandexGPT.model_rebuild()
