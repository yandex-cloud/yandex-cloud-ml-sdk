from __future__ import annotations

import dataclasses
from typing import Any

from yandex_cloud_ml_sdk._types.result import BaseProtoResult, ProtoMessageTypeT_contra


@dataclasses.dataclass(frozen=True)
class BaseMessage(BaseProtoResult[ProtoMessageTypeT_contra]):
    """
    Abstract class for messages in Yandex Cloud ML Assistant service.

    Provides core functionality for all message types including:
    - Storage and processing of message parts (text, citations, etc.)
    - Basic text content operations
    - Protocol buffer support via BaseProtoResult[ProtoMessageTypeT_contra]

    Extended by:
    - Message: Complete assistant messages
    - PartialMessage: Intermediate message content during streaming
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
