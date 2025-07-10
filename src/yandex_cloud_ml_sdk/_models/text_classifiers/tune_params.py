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
    """This class encapsulates the parameters used for tuning text classification models,
    supporting both multiclass and multilabel classification types.
    """
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

    #: the type of classification to be used (should be one of 'multilabel', 'multiclass', or 'binary'.)
    classification_type: ClassificationTuningTypes | None = None
    #: random seed for reproducibility
    seed: int | None = None
    #: a learning rate for the tuning process
    lr: float | None = None
    #: a number of samples to use for tuning
    n_samples: int | None = None
    #:  any additional arguments required for tuning
    additional_arguments: str | None = None
