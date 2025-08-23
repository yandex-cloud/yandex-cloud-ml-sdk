# pylint: disable=protected-access
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any, Generic

from typing_extensions import Self, override

from yandex_cloud_ml_sdk._models.completions.config import CompletionTool
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall, ToolCall, ToolCallTypeT
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin, ModelSyncStreamMixin
from yandex_cloud_ml_sdk._types.schemas import ResponseType, http_schema_from_response_format
from yandex_cloud_ml_sdk._types.tools.tool_choice import ToolChoiceType
from yandex_cloud_ml_sdk._types.tools.tool_choice import coerce_to_json as coerce_tool_choice_to_json
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .config import ChatModelConfig, ChatReasoningModeType
from .message import ChatMessageInputType, messages_to_json
from .result import ChatModelResult


class BaseChatModel(
    Generic[ToolCallTypeT],
    ModelSyncMixin[ChatModelConfig, ChatModelResult[ToolCallTypeT]],
    ModelSyncStreamMixin[ChatModelConfig, ChatModelResult[ToolCallTypeT]],
):
    _config_type = ChatModelConfig
    _result_type: type[ChatModelResult[ToolCallTypeT]]
    _proto_result_type = None

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        temperature: UndefinedOr[float] | None = UNDEFINED,
        max_tokens: UndefinedOr[int] | None = UNDEFINED,
        reasoning_mode: UndefinedOr[ChatReasoningModeType] | None = UNDEFINED,
        response_format: UndefinedOr[ResponseType] | None = UNDEFINED,
        tools: UndefinedOr[Sequence[CompletionTool] | CompletionTool] = UNDEFINED,
        parallel_tool_calls: UndefinedOr[bool] = UNDEFINED,
        tool_choice: UndefinedOr[ToolChoiceType] = UNDEFINED,
    ) -> Self:
        return super().configure(
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_mode=reasoning_mode,
            response_format=response_format,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            tool_choice=tool_choice,
        )

    def _build_request_json(self, messages: ChatMessageInputType, stream: bool) -> dict[str, Any]:
        result = {
            'model': self._uri,
            'messages': messages_to_json(messages),
            'stream': stream,
        }

        c = self._config

        if c.temperature is not None:
            result['temperature'] = c.temperature

        if c.max_tokens is not None:
            result['max_tokens'] = c.max_tokens

        if c.response_format is not None:
            response_format = result['response_format'] = http_schema_from_response_format(c.response_format)
            if response_format['type'] == 'json_schema':
                json_schema = response_format['json_schema']
                if 'name' not in json_schema:
                    raise ValueError(
                        '"name" field is required in json_schema response_format if you are using it in sdk.chat domain'
                    )
        if c.reasoning_mode is not None:
            result['reasoning_effort'] = c.reasoning_mode.value

        if c.tools is not None:
            result['tools'] = [tool._to_json() for tool in c.tools]

        if c.parallel_tool_calls is not None:
            result['parallel_tool_calls'] = c.parallel_tool_calls

        if c.tool_choice is not None:
            result['tool_choice'] = coerce_tool_choice_to_json(c.tool_choice)

        return result

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> ChatModelResult[ToolCallTypeT]:
        async with self._client.httpx_for_service('http_completions', timeout) as client:
            response = await client.post(
                '/chat/completions',
                json=self._build_request_json(messages, stream=False),
                timeout=timeout,
            )
            response.raise_for_status()

        return ChatModelResult._from_json(data=response.json(), sdk=self._sdk)

    @override
    # pylint: disable-next=arguments-differ,too-many-locals
    async def _run_stream(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> AsyncIterator[ChatModelResult[ToolCallTypeT]]:
        role: str = ""
        content_buffer: str = ""
        reasoning_content_buffer: str | None = ""
        last_finish_reason: str | None = None

        async for sse in self._client.sse_stream(
            'http_completions',
            method='POST',
            url='/chat/completions',
            json=self._build_request_json(messages, stream=True),
            timeout=timeout
        ):
            # {'id': '...', 'object': 'chat.completion.chunk', 'created': ..., 'model': '...', 'choices': [{'index': 0, 'delta': {'content': '...'}}]}
            data = sse.json()

            choices: list[dict[str, Any]] | None = data.get('choices')
            if not choices:
                # We are making pseudo-choices which have exactly same content as a last chunk;
                # qwen3-235b-a22b-fp8, for example, producing empty choices at last chunk which have usage instead
                choices = data['choices'] = [{
                    'index': 0,
                    'delta': {'content': ''}
                }]

            # NB: We will take the 'delta' dict and modify it inplace
            choice = choices[0]
            delta = choice.get('delta', {})
            assert isinstance(delta, dict)
            if not delta:
                # qwen3-235b-a22b-fp8 sometimets producing an empty delta,
                # but with our model we need to put it explicitly
                delta = data['choices'][0]['delta'] = {'content': ''}

            if 'tool_calls' in delta:
                raise NotImplementedError('tool calls not implemented in SDK in stream mode yet')

            # By our model each chunk have to have an role, but in this stream only first one have
            if new_role := delta.get('role'):
                role = new_role
            if role:
                delta['role'] = role

            # qwen3-235b-a22b-fp8 have a first message without content, only with role
            content = delta['content'] = delta.get('content', '')
            content_buffer += content

            reasoning_content = delta.get('reasoning_content')
            if reasoning_content is not None:
                reasoning_content_buffer = reasoning_content_buffer or ""
                reasoning_content_buffer += reasoning_content

            if reasoning_content_buffer:
                delta['reasoning_text'] = reasoning_content_buffer

            finish_reason: str | None = choice.get('finish_reason')  # type: ignore[assignment]
            # qwen3-235b-a22b-fp8 in usage message (which follows the "last chunk")
            # do not have a finish_reason field and
            # I don't like we are producing chunk with a "null" finish_reason
            # which we translating into "partial" status after a chunk with real finish reason
            # so we are inheriting finish_reason in case it was already produced before
            choice['finish_reason'] = finish_reason or last_finish_reason
            if finish_reason:
                last_finish_reason = finish_reason
            # In our model we operating with growing prefixes instead of deltas;
            # However, in case of content_filter we need to pass a whole content instead of a prefix
            if finish_reason and finish_reason.lower() == 'content_filter':
                delta['text'] = content
            else:
                delta['text'] = content_buffer

            data['choices'] = [choice]

            yield self._result_type._from_json(data=data, sdk=self._sdk)


class AsyncChatModel(
    BaseChatModel[AsyncToolCall],
):
    _result_type = ChatModelResult[AsyncToolCall]

    async def run(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> ChatModelResult[AsyncToolCall]:
        return await self._run(
            messages=messages,
            timeout=timeout
        )

    async def run_stream(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> AsyncIterator[ChatModelResult[AsyncToolCall]]:
        async for result in self._run_stream(
            messages=messages,
            timeout=timeout
        ):
            yield result


class ChatModel(
    BaseChatModel[ToolCall],
):
    _result_type = ChatModelResult[ToolCall]
    __run = run_sync(BaseChatModel._run)
    __run_stream = run_sync_generator(BaseChatModel._run_stream)

    def run(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> ChatModelResult[ToolCall]:
        return self.__run(
            messages=messages,
            timeout=timeout
        )

    def run_stream(
        self,
        messages: ChatMessageInputType,
        *,
        timeout=180,
    ) -> Iterator[ChatModelResult[ToolCall]]:
        yield from self.__run_stream(
            messages=messages,
            timeout=timeout
        )
