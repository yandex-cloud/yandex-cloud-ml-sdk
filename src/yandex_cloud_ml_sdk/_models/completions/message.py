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
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


@runtime_checkable
class TextMessageWithToolCallsProtocol(TextMessageProtocol, Protocol):
    """
    A class with a protocol which defines a text message structure with associated tool calls.
    The protocol extends the TextMessageProtocol and requires a list of tool calls.
    """
    tool_calls: ToolCallList


class FunctionResultMessageDict(TypedDict):
    """
    A class with the TypedDict representing the structure of a function result message.
    The dictionary contains the role of the message sender and the results of tool calls.
    """
    role: NotRequired[str]
    tool_results: Required[Iterable[ToolResultDictType]]


class _ProtoMessageKwargs(TypedDict):
    role: Required[str]
    text: NotRequired[str]
    tool_result_list: NotRequired[ProtoCompletionsToolResultList]
    tool_call_list: NotRequired[ProtoCompletionsToolCallList]

#: a type alias for a message that can either be a standard message or a function result message.
CompletionsMessageType = Union[MessageType, FunctionResultMessageDict]
#: a type alias for input that can be either a single completion message or a collection (i.e. an iterable) of completion messages.
MessageInputType = Union[CompletionsMessageType, Iterable[CompletionsMessageType]]


def message_to_proto(message: CompletionsMessageType) -> ProtoMessage:
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

    return ProtoMessage(**kwargs)


def messages_to_proto(messages: MessageInputType) -> list[ProtoMessage]:
    """:meta private:"""
    msgs: tuple[CompletionsMessageType, ...] = coerce_tuple(
        messages,
        (dict, str, TextMessageProtocol),  # type: ignore[arg-type]
    )

    result: list[ProtoMessage] = []

    for message in msgs:
        result.append(
            message_to_proto(message)
        )

    return result
