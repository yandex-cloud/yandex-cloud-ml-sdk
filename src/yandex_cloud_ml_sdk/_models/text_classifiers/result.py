from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Sequence, TypeVar, overload

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_classification.text_classification_service_pb2 import (
    FewShotTextClassificationResponse, TextClassificationResponse
)

from yandex_cloud_ml_sdk._types.result import BaseProtoResult

from .types import TextClassificationLabel

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


TextClassificationResponseT = TypeVar(
    'TextClassificationResponseT',
    TextClassificationResponse,
    FewShotTextClassificationResponse
)


@dataclass(frozen=True)
class TextClassifiersModelResultBase(BaseProtoResult[TextClassificationResponseT], Sequence, Generic[TextClassificationResponseT]):
    """A class for text classifiers model results.
    It represents the common structure for the results returned by text classification models.
    """
    #: a tuple containing the predicted labels
    predictions: tuple[TextClassificationLabel, ...]
    #: the version of the model used for prediction
    model_version: str
    #: Number of input tokens provided to the model.
    input_tokens: int

    @classmethod
    def _from_proto(cls, *, proto: TextClassificationResponseT, sdk: BaseSDK) -> Self:  # pylint: disable=unused-argument
        predictions = tuple(
            TextClassificationLabel(
                label=p.label,
                confidence=p.confidence
            ) for p in proto.predictions
        )

        return cls(
            predictions=predictions,
            model_version=proto.model_version,
            input_tokens = proto.input_tokens
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
