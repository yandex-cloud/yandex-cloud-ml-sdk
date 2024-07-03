from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2 import TextEmbeddingResponse

from yandex_cloud_ml_sdk._types.result import BaseResult


@dataclass(frozen=True)
class TextEmbeddingsModelResult(BaseResult[TextEmbeddingResponse], Sequence):
    _proto_result_type = TextEmbeddingResponse

    embedding: tuple[float, ...]
    num_tokens: int
    model_version: str

    @classmethod
    def _from_proto(cls, message: TextEmbeddingResponse) -> Self:
        return cls(
            embedding=tuple(message.embedding),
            num_tokens=message.num_tokens,
            model_version=message.model_version,
        )

    def __len__(self) -> int:
        return len(self.embedding)

    @overload
    def __getitem__(self, index: int, /) -> float:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[float, ...]:
        pass

    def __getitem__(self, index, /):
        return self.embedding[index]

    def __array__(self, dtype=None, copy=None):
        import numpy  # pylint: disable=import-outside-toplevel

        if copy is False:
            raise ValueError(
                "`copy=False` isn't supported. A copy is always created."
            )

        return numpy.array(self.embedding, dtype=dtype)
