from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict, Union, runtime_checkable

from typing_extensions import NotRequired, Required, TypeAlias


@dataclass(frozen=True)
class TextMessage:
    role: str
    text: str


@runtime_checkable
class TextMessageProtocol(Protocol):
    @property
    def role(self) -> str: ...

    @property
    def text(self) -> str: ...


class TextMessageDict(TypedDict):
    role: NotRequired[str]
    text: Required[str]


MessageType: TypeAlias = Union[TextMessage, TextMessageDict, TextMessageProtocol, str]


def coerce_to_text_message_dict(message: MessageType) -> TextMessageDict:
    if isinstance(message, (TextMessage, TextMessageProtocol)):
        return {
            'text': message.text,
            'role': message.role,
        }

    if isinstance(message, dict) and 'text' in message:
        return message

    if isinstance(message, str):
        return {
            'text': message,
        }

    raise TypeError(f'{message=!r} should be str, dict with "text" key or TextMessage instance')
