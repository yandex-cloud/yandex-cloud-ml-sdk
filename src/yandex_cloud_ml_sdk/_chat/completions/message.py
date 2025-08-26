from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict, Union, cast

from typing_extensions import NotRequired, Required

from yandex_cloud_ml_sdk._models.completions.message import (
    FunctionResultMessageDict, MessageInputType, MessageType, TextMessageWithToolCallsProtocol
)
from yandex_cloud_ml_sdk._tools.tool_result import ToolResultDictType
from yandex_cloud_ml_sdk._types.json import JsonObject
from yandex_cloud_ml_sdk._types.message import TextMessageDict, TextMessageProtocol
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


class ChatFunctionResultMessageDict(TypedDict):
    role: NotRequired[str]
    tool_call_id: Required[str]
    content: Required[str]


ChatCompletionsMessageType = Union[MessageType, ChatFunctionResultMessageDict, MessageInputType]
ChatMessageInputType = Union[ChatCompletionsMessageType, Iterable[ChatCompletionsMessageType]]


def message_to_json(message: ChatCompletionsMessageType, tool_name_ids: dict[str, str]) -> JsonObject | list[JsonObject]:
    if isinstance(message, str):
        return {'role': 'user', 'content': message}

    if isinstance(message, TextMessageProtocol):
        if isinstance(message, TextMessageWithToolCallsProtocol) and message.tool_calls:
            return {
                'role': message.role,
                'tool_calls': [
                    # pylint: disable-next=protected-access
                    tool_call._json_origin for tool_call in message.tool_calls
                ]
            }

        return {
            "content": message.text,
            "role": message.role,
        }
    if isinstance(message, dict):
        text = message.get('text') or message.get('content', '')
        assert isinstance(text, str)

        if tool_call_id := message.get('tool_call_id'):
            assert isinstance(tool_call_id, str)
            message = cast(ChatFunctionResultMessageDict, message)
            role = message.get('role', 'tool')
            return {
                'role': role,
                'content': text,
                'tool_call_id': tool_call_id,
            }

        if text:
            message = cast(TextMessageDict, message)
            role = message.get('role', 'user')
            return {
                'content': text,
                'role': role
            }

        if tool_results := message.get('tool_results'):
            assert isinstance(tool_results, list)
            message = cast(FunctionResultMessageDict, message)

            role = message.get('role', 'tool')
            result: list[JsonObject] = []
            for tool_result in tool_results:
                tool_result = cast(ToolResultDictType, tool_result)
                name = tool_result['name']
                content = tool_result['content']

                id_ = tool_name_ids.get(name)
                if not id_:
                    raise ValueError(
                        f'failed to find tool call with name "{name}" in previous messages for message {message}'
                    )

                result.append({
                    'role': role,
                    'content': content,
                    'tool_call_id': id_,
                })

            return result

        raise TypeError(f'{message=!r} should have a "text", "content" or "tool_call_id" key')

    raise TypeError(f'{message=!r} should be str, dict with "text" or "tool_call_id" key or TextMessage instance')


def messages_to_json(messages: ChatMessageInputType) -> list[JsonObject]:
    """:meta private:"""
    msgs: tuple[ChatCompletionsMessageType, ...] = coerce_tuple(
        messages,
        (dict, str, TextMessageProtocol),  # type: ignore[arg-type]
    )
    result: list[JsonObject] = []

    last_tool_call_ids: dict[str, str] = {}

    for message in msgs:
        converted = message_to_json(message, last_tool_call_ids)
        if isinstance(converted, list):
            result.extend(converted)
            continue

        assert isinstance(converted, dict)
        if tool_calls := converted.get('tool_calls'):
            assert isinstance(tool_calls, list)
            for tool_call in tool_calls:
                assert isinstance(tool_call, dict)

                id_ = tool_call.get('id')
                assert isinstance(id_, str)

                function = tool_call.get('function', {})
                assert isinstance(function, dict)
                name = function.get('name')
                assert isinstance(name, str)

                last_tool_call_ids[name] = id_
        else:
            last_tool_call_ids = {}

        result.append(converted)

    return result
