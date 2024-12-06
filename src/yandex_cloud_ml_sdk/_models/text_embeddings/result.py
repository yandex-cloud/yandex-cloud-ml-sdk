from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence, cast, overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2 import TextEmbeddingResponse

from yandex_cloud_ml_sdk._types.result import BaseResult, ProtoMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class TextEmbeddingsModelResult(BaseResult, Sequence):
    embedding: tuple[float, ...]
    num_tokens: int
    model_version: str

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
        proto = cast(TextEmbeddingResponse, proto)
        return cls(
            embedding=tuple(proto.embedding),
            num_tokens=proto.num_tokens,
            model_version=proto.model_version,
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
