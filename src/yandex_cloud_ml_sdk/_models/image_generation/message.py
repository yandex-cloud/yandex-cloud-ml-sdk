from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, TypedDict, Union, cast, runtime_checkable

from typing_extensions import NotRequired
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_pb2 import Message as ProtoMessage


@dataclass(frozen=True)
class ImageMessage:
    text: str
    weight: float | None = None


class ImageMessageDict(TypedDict):
    text: str
    weight: NotRequired[float]


# NB: it supports _messages.message.Message and _models.completions.message.TextMessage
@runtime_checkable
class AnyMessage(Protocol):
    text: str


ImageMessageType = Union[ImageMessage, ImageMessageDict, AnyMessage, str]
ImageMessageInputType = Union[ImageMessageType, Iterable[ImageMessageType]]


def messages_to_proto(messages: ImageMessageInputType) -> list[ProtoMessage]:
    msgs: Iterable[ImageMessageType]
    if isinstance(messages, (dict, str, ImageMessage, AnyMessage)):
        # NB: dict is also Iterable, so techically messages could be a dict[MessageType, str]
        # and we are wrongly will get into this branch.
        # At least mypy thinks so.
        # In real life, messages could be list, tuple, iterator, generator but nothing else.

        msgs = [messages]  # type: ignore[list-item]
    else:
        msgs = messages

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
