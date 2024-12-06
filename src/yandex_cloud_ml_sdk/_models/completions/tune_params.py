from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

# pylint: disable=no-name-in-module
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import TextToTextCompletionTuningParams

from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams


@dataclass(frozen=True)
class GPTModelTuneParams(BaseTuningParams[TextToTextCompletionTuningParams]):
    _proto_tuning_params_type = TextToTextCompletionTuningParams
    _proto_tuning_argument_name: ClassVar[str] = 'text_to_text_completion'

    seed: int | None = None
    lr: float | None = None
    n_samples: int | None = None
    additional_arguments: str | None = None
