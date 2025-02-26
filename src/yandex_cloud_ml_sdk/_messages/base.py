from __future__ import annotations

import dataclasses
from typing import Any

from yandex_cloud_ml_sdk._types.result import BaseResult


@dataclasses.dataclass(frozen=True)
class BaseMessage(BaseResult):
    parts: tuple[Any, ...]

    @property
    def text(self):
        return '\n'.join(
            part for part in self.parts
            if isinstance(part, str)
        )
