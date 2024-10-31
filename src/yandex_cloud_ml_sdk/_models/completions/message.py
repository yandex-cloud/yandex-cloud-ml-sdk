from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypedDict, Union, cast

# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Message as ProtoMessage


@dataclass(frozen=True)
class TextMessage:
    role: str
    text: str


class TextMessageDict(TypedDict):
    role: str
    text: str

MessageType = Union[TextMessage, TextMessageDict, str]
MessageInputType = Union[MessageType, Iterable[MessageType]]


def messages_to_proto(messages: MessageInputType) -> list[ProtoMessage]:
    msgs: Iterable[MessageType]
    if isinstance(messages, (dict, str, TextMessage)):
        # NB: dict is also Iterable, so techically messages could be a dict[MessageType, str]
        # and we are wrongly will get into this branch.
        # At least mypy thinks so.
        # In real life, messages could be list, tuple, iterator, generator but nothing else.

        msgs = [messages]  # type: ignore[list-item]
    else:
        msgs = messages

    result: list[ProtoMessage] = []

    for message in msgs:
        kwargs: TextMessageDict
        if isinstance(message, str):
            kwargs = {'role': 'user', 'text': message}
        elif isinstance(message, TextMessage):
            kwargs = {'role': message.role, 'text': message.text}
        elif isinstance(message, dict) and 'role' in message and 'text' in message:
            kwargs = cast(TextMessageDict, message)
        else:
            raise TypeError(f'{message=} should be str, {{"role": str, "text": str}} dict or TextMessage instance')

        result.append(
            ProtoMessage(**kwargs)
        )

    return result
