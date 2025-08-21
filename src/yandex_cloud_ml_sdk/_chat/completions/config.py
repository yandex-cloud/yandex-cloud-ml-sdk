from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

from typing_extensions import Self

from yandex_cloud_ml_sdk._models.completions.config import CompletionTool, GPTModelConfig
from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


class ChatReasoningMode(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

    @classmethod
    def _coerce(cls, value: ChatReasoningModeType) -> Self:
        if isinstance(value, cls):
            return value

        assert isinstance(value, str)
        return cls(value.lower())


ChatReasoningModeType = Union[str, ChatReasoningMode]


@dataclass(frozen=True)
class ChatModelConfig(GPTModelConfig):
    reasoning_mode: ChatReasoningMode | None = None
    tools: tuple[CompletionTool, ...] | None = None

    def _replace(self, **kwargs: Any) -> Self:
        if reasoning_mode := kwargs.get('reasoning_mode'):
            kwargs['reasoning_mode'] = ChatReasoningMode._coerce(reasoning_mode)

        if tools := kwargs.get('tools'):
            kwargs['tools'] = coerce_tuple(tools, BaseTool)  # type: ignore[type-abstract]

        return super()._replace(**kwargs)
