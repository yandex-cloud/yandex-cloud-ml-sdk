from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2 import (
    FewShotTextClassificationResponse, TextClassificationResponse
)

from yandex_cloud_ml_sdk._types.result import BaseResult

from .types import TextClassificationLabel

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


TextClassificationResponseT = TypeVar(
    'TextClassificationResponseT',
    TextClassificationResponse,
    FewShotTextClassificationResponse
)


@dataclass(frozen=True)
class TextClassifiersModelResultBase(BaseResult[TextClassificationResponseT], Sequence):
    predictions: tuple[TextClassificationLabel, ...]
    model_version: str

    @classmethod
    def _from_proto(cls, proto: TextClassificationResponseT, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
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
    _proto_result_type = TextClassificationResponse


@dataclass(frozen=True)
class FewShotTextClassifiersModelResult(TextClassifiersModelResultBase[FewShotTextClassificationResponse]):
    _proto_result_type = FewShotTextClassificationResponse
