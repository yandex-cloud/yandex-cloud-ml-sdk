from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypedDict, Union, cast, runtime_checkable

from typing_extensions import NotRequired, Required
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Message as ProtoMessage

from yandex_cloud_ml_sdk._tools.tool_call_list import ProtoCompletionsToolCallList, ToolCallList
from yandex_cloud_ml_sdk._tools.tool_result import (
    ProtoCompletionsToolResultList, ToolResultDictType, tool_results_to_proto
)
from yandex_cloud_ml_sdk._types.message import MessageType, TextMessageDict, TextMessageProtocol


@runtime_checkable
class TextMessageWithToolCallsProtocol(TextMessageProtocol, Protocol):
    tool_calls: ToolCallList


class FunctionResultMessageDict(TypedDict):
    role: NotRequired[str]
    tool_results: Required[Iterable[ToolResultDictType]]


class _ProtoMessageKwargs(TypedDict):
    role: Required[str]
    text: NotRequired[str]
    tool_result_list: NotRequired[ProtoCompletionsToolResultList]
    tool_call_list: NotRequired[ProtoCompletionsToolCallList]


CompletionsMessageType = Union[MessageType, FunctionResultMessageDict]
MessageInputType = Union[CompletionsMessageType, Iterable[CompletionsMessageType]]


def messages_to_proto(messages: MessageInputType) -> list[ProtoMessage]:
    msgs: Iterable[CompletionsMessageType]
    if isinstance(messages, (dict, str, TextMessageProtocol)):
        # NB: dict is also Iterable, so techically messages could be a dict[MessageType, str]
        # and we are wrongly will get into this branch.
        # At least mypy thinks so.
        # In real life, messages could be list, tuple, iterator, generator but nothing else.

        msgs = [messages]  # type: ignore[list-item]
    else:
        assert isinstance(messages, Iterable)
        msgs = messages

    result: list[ProtoMessage] = []

    for message in msgs:
        kwargs: _ProtoMessageKwargs
        if isinstance(message, str):
            kwargs = {'role': 'user', 'text': message}
        elif isinstance(message, TextMessageProtocol):
            if isinstance(message, TextMessageWithToolCallsProtocol) and message.tool_calls:
                # pylint: disable=protected-access
                kwargs = {'role': message.role, 'tool_call_list': message.tool_calls._proto_origin}
            else:
                kwargs = {'role': message.role, 'text': message.text}
        elif isinstance(message, dict):
            role = message.get('role', 'user')
            if 'text' in message:
                message = cast(TextMessageDict, message)
                kwargs = {'role': role, 'text': message['text']}
            elif 'tool_results' in message:
                message = cast(FunctionResultMessageDict, message)
                tool_results = tool_results_to_proto(message['tool_results'], proto_type=ProtoCompletionsToolResultList)
                kwargs = {
                    'role': role,
                    'tool_result_list': tool_results,
                }
            else:
                raise TypeError(f'{message=!r} should have a "text" or "tool_results" key')
        else:
            raise TypeError(f'{message=!r} should be str, dict with "text" or "tool_results" key or TextMessage instance')

        result.append(
            ProtoMessage(**kwargs)
        )

    return result
