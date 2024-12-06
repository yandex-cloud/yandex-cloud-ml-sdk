from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Sequence, TypeVar, cast, overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2 import (
    FewShotTextClassificationResponse, TextClassificationResponse
)

from yandex_cloud_ml_sdk._types.result import BaseResult, ProtoMessage

from .types import TextClassificationLabel

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


TextClassificationResponseT = TypeVar(
    'TextClassificationResponseT',
    TextClassificationResponse,
    FewShotTextClassificationResponse
)


@dataclass(frozen=True)
class TextClassifiersModelResultBase(BaseResult, Sequence, Generic[TextClassificationResponseT]):
    predictions: tuple[TextClassificationLabel, ...]
    model_version: str

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
        proto = cast(TextClassificationResponseT, proto)
        predictions = tuple(
            TextClassificationLabel(
                label=p.label,
                confidence=p.confidence
            ) for p in proto.predictions
        )

        return cls(
            predictions=predictions,
            model_version=proto.model_version,
        )

    def __len__(self) -> int:
        return len(self.predictions)

    @overload
    def __getitem__(self, index: int, /) -> TextClassificationLabel:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[TextClassificationLabel, ...]:
        pass

    def __getitem__(self, index, /):
        return self.predictions[index]


@dataclass(frozen=True)
class TextClassifiersModelResult(TextClassifiersModelResultBase[TextClassificationResponse]):
    pass


@dataclass(frozen=True)
class FewShotTextClassifiersModelResult(TextClassifiersModelResultBase[FewShotTextClassificationResponse]):
    pass
