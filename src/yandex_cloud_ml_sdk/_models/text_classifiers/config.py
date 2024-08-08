from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig

from .types import TextClassificationSample


@dataclass(frozen=True)
class TextClassifiersModelConfig(BaseModelConfig):
    task_description: str | None = None
    labels: Sequence[str] | None = None
    samples: Sequence[TextClassificationSample] | None = None
