from __future__ import annotations

from dataclasses import dataclass

# pylint: disable=no-name-in-module
from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import TextToTextCompletionTuningParams

from yandex_cloud_ml_sdk._types.tuning.params import BaseTuningParams


@dataclass(frozen=True)
class GPTModelTuneParams(BaseTuningParams[TextToTextCompletionTuningParams]):
    _proto_tuning_params_type = TextToTextCompletionTuningParams

    seed: int | None = None
    lr: float | None = None
    n_samples: int | None = None
    additional_arguments: str | None = None
