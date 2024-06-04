from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Token as ProtoToken


@dataclass(frozen=True)
class Token:
    id: int
    special: bool
    text: str

    @classmethod
    def _from_proto(cls, message: ProtoToken) -> Self:
        return cls(
            id=message.id,
            special=message.special,
            text=message.text
        )
