from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import CompletionResponse

from yandex_cloud_ml_sdk._types.result import BaseResult

from .message import TextMessage


@dataclass(frozen=True)
class Usage:
    input_text_tokens: int
    completion_tokens: int
    total_tokens: int


class AlternativeStatus(Enum):
    UNSPECIFIED = 0
    PARTIAL = 1
    TRUNCATED_FINAL = 2
    FINAL = 3
    CONTENT_FILTER = 4

    UNKNOWN = -1

    @classmethod
    def from_proto_field(cls, status: int):
        try:
            return cls(status)
        except ValueError:
            return cls(-1)


@dataclass(frozen=True)
class Alternative(TextMessage):
    status: AlternativeStatus


@dataclass(frozen=True)
class GPTModelResult(BaseResult[CompletionResponse], Sequence):
    _proto_result_type = CompletionResponse

    alternatives: tuple[Alternative, ...]
    usage: Usage
    model_version: str

    @classmethod
    def _from_proto(cls, message: CompletionResponse) -> Self:
        alternatives = tuple(
            Alternative(
                role=alternative.message.role,
                text=alternative.message.text,
                status=AlternativeStatus.from_proto_field(alternative.status),
            ) for alternative in message.alternatives
        )
        usage = Usage(
            input_text_tokens=message.usage.input_text_tokens,
            completion_tokens=message.usage.completion_tokens,
            total_tokens=message.usage.total_tokens,
        )

        return cls(
            alternatives=alternatives,
            usage=usage,
            model_version=message.model_version,
        )

    def __len__(self):
        return len(self.alternatives)

    @overload
    def __getitem__(self, index: int, /) -> Alternative:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[Alternative, ...]:
        pass

    def __getitem__(self, index, /):
        return self.alternatives[index]
