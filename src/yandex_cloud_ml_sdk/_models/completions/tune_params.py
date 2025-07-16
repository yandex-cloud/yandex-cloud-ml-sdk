from __future__ import annotations

from dataclasses import dataclass

# pylint: disable=no-name-in-module
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import TextToTextCompletionTuningParams

from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams


@dataclass(frozen=True)
class GPTModelTuneParams(BaseTuningParams):
    """This class encapsulates the parameters used for tuning a GPT model
    in a text-to-text completion context."""
    @property
    def _proto_tuning_params_type(self):
        return TextToTextCompletionTuningParams

    @property
    def _proto_tuning_argument_name(self):
        return 'text_to_text_completion'

    #: random seed for reproducibility
    seed: int | None = None
    #: a learning rate for the tuning process
    lr: float | None = None
    #: a number of samples to use for tuning
    n_samples: int | None = None
    #: any additional arguments required for tuning
    additional_arguments: str | None = None
