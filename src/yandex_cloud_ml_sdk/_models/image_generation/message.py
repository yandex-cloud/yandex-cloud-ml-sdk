from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, TypedDict, Union, cast, runtime_checkable

from typing_extensions import NotRequired
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_pb2 import Message as ProtoMessage

from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


@dataclass(frozen=True)
class ImageMessage:
    """
    This class represents a message for using in image generation models with optional weight field.
    """
    #: the text content of the message for using in image generation models
    text: str
    #: the weight associated with the message
    weight: float | None = None


class ImageMessageDict(TypedDict):
    """
    The class with TypedDict representing the structure of an image message.
    """
    text: str
    weight: NotRequired[float]


# NB: it supports _messages.message.Message and _models.completions.message.TextMessage
@runtime_checkable
class AnyMessage(Protocol):
    """
    The class with a protocol which defines an object with a text field.
    The protocol can be used to check if an object has a text attribute.
    """
    text: str

#: type alias for different types of messages that can be processed by image generation models
ImageMessageType = Union[ImageMessage, ImageMessageDict, AnyMessage, str]
#: type alias for input types accepted by the `messages_to_proto` function
ImageMessageInputType = Union[ImageMessageType, Iterable[ImageMessageType]]


def messages_to_proto(messages: ImageMessageInputType) -> list[ProtoMessage]:
    """:meta private:"""
    msgs: tuple[ImageMessageType] = coerce_tuple(  # type: ignore[assignment]
        messages,
        (dict, str, ImageMessage, AnyMessage)  # type: ignore[arg-type]
    )

    result: list[ProtoMessage] = []

    for message in msgs:
        kwargs: ImageMessageDict
        if isinstance(message, str):
            kwargs = {'text': message}
        elif isinstance(message, AnyMessage):
            kwargs =  {'text': message.text}
            if weight := getattr(message, 'weight', None):
                kwargs['weight'] = weight
        elif isinstance(message, dict) and 'text' in message:
            kwargs = cast(ImageMessageDict, message)
        else:
            raise TypeError(
                f'{message=} should be str, {{["weight": float], "text": str}} dict '
                'or object with a `text: str` field'
            )

        result.append(
            ProtoMessage(**kwargs)
        )

    return result
