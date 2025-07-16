from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Token as ProtoToken


@dataclass(frozen=True)
class Token:
    """This class encapsulates the properties of a token
    and represents it in a text processing context."""
    #: a unique identifier for the token
    id: int
    #: a flag indicating if the token is a special one
    special: bool
    #: the textual representation of the token
    text: str

    @classmethod
    def _from_proto(cls, message: ProtoToken) -> Self:
        return cls(
            id=message.id,
            special=message.special,
            text=message.text
        )
