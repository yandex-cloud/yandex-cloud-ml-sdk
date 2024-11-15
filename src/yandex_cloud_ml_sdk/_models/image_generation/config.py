from __future__ import annotations

from dataclasses import dataclass

from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class ImageGenerationModelConfig(BaseModelConfig):
    seed: int | None = None
    width_ratio: int | None = None
    height_ratio: int | None = None
    mime_type: str | None = None
