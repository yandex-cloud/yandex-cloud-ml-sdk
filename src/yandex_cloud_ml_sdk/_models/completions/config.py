from __future__ import annotations

from dataclasses import dataclass

from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class GPTModelConfig(BaseModelConfig):
    temperature: float | None = None
    max_tokens: int | None = None
