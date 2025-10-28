from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict, Union, runtime_checkable

from typing_extensions import NotRequired, Required, TypeAlias


@dataclass(frozen=True)
class TextMessage:
    """
    Immutable text message representation.

    Class represents a text message with a role and content.
    This is the primary message type used throughout the SDK.
    """
    #: The role of the message sender (e.g., 'user', 'assistant', 'system')
    role: str
    #: The actual text content of the message
    text: str


@runtime_checkable
class TextMessageProtocol(Protocol):
    """
    Protocol for text message-like objects.

    This protocol defines the interface that any text message object should implement.
    It can be used for type checking and duck typing with objects that have role and text properties.
    The protocol is runtime checkable, meaning isinstance() checks will work.
    """

    @property
    def role(self) -> str:
        """Get the role of the message sender."""
        ...

    @property
    def text(self) -> str:
        """Get the text content of the message."""
        ...

class TextMessageDict(TypedDict):
    """
    Typed dictionary representation of a text message.

    A TypedDict that represents a text message as a dictionary structure.
    The role field is optional while text field is required.

    :param role: Optional role of the message sender
    :param text: Required text content of the message
    """
    role: NotRequired[str]
    text: Required[str]


#: Type alias for all supported message types.
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
