from __future__ import annotations

from dataclasses import dataclass

from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class TextEmbeddingsModelConfig(BaseModelConfig):
    #: dimensions of output vector
    dimensions: int | None = None
