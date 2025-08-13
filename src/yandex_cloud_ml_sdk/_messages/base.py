from __future__ import annotations

import dataclasses
from typing import Any

from yandex_cloud_ml_sdk._types.result import BaseProtoResult, ProtoMessageTypeT_contra


@dataclasses.dataclass(frozen=True)
class BaseMessage(BaseProtoResult[ProtoMessageTypeT_contra]):
    parts: tuple[Any, ...]

    @property
    def text(self) -> str:
        return '\n'.join(
            part for part in self.parts
            if isinstance(part, str)
        )
