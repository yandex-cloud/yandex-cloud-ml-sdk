from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# pylint: disable=no-name-in-module
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    TextClassificationMulticlassParams, TextClassificationMultilabelParams
)

from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams

ClassificationTuningTypes = Literal['multilabel', 'multiclass', 'binary']


@dataclass(frozen=True)
class TextClassifiersModelTuneParams(BaseTuningParams):
    @property
    def _proto_tuning_params_type(
        self
    ) -> type[TextClassificationMulticlassParams] | type[TextClassificationMultilabelParams]:
        if self.classification_type == 'multiclass':
            return TextClassificationMulticlassParams

        return TextClassificationMultilabelParams

    @property
    def _proto_tuning_argument_name(
        self
    ) -> Literal['text_classification_multilabel', 'text_classification_multiclass']:
        if self.classification_type == 'multiclass':
            return 'text_classification_multiclass'

        return 'text_classification_multilabel'

    @property
    def _ignored_fields(self):
        return super()._ignored_fields + ('classification_type', )

    def __post_init__(self):
        if self.classification_type not in ('multiclass', 'multilabel', 'binary'):
            raise ValueError(
                f'classification_type must be {ClassificationTuningTypes}, got {self.classification_type}'
            )

    classification_type: ClassificationTuningTypes | None = None
    seed: int | None = None
    lr: float | None = None
    n_samples: int | None = None
    additional_arguments: str | None = None
