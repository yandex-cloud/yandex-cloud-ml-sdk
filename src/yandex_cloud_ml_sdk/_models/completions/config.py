from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union

# pylint: disable=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ReasoningOptions as ProtoReasoningOptions

from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig
from yandex_cloud_ml_sdk._types.structured_output import ResponseType
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase

_m = ProtoReasoningOptions.ReasoningMode


class ReasoningMode(ProtoEnumBase, Enum):
    REASONING_MODE_UNSPECIFIED = _m.REASONING_MODE_UNSPECIFIED
    DISABLED = _m.DISABLED
    ENABLED_HIDDEN = _m.ENABLED_HIDDEN


ReasoningModeType = Union[int, str, ReasoningMode]


@dataclass(frozen=True)
class GPTModelConfig(BaseModelConfig):
    temperature: float | None = None
    max_tokens: int | None = None
    reasoning_mode: ReasoningModeType | None = None
    response_format: ResponseType | None = None
