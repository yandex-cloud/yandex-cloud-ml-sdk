from __future__ import annotations

import dataclasses
from typing import Any

from yandex_cloud_ml_sdk._types.result import BaseResult


@dataclasses.dataclass(frozen=True)
class BaseMessage(BaseResult):
    """
    Base class for all message types in the SDK.
    """
    #: Tuple containing message parts (can be strings or other types)
    parts: tuple[Any, ...]

    @property
    def text(self) -> str:
        """
        Get concatenated string of all text parts in the message by joining all string parts.
        """
        return '\n'.join(
            part for part in self.parts
            if isinstance(part, str)
        )
