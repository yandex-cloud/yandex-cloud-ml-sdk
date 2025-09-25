from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Union

from typing_extensions import Self

from yandex_cloud_ml_sdk._models.completions.config import CompletionTool, GPTModelConfig
from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._types.schemas import QueryType
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


class ChatReasoningMode(str, Enum):
    """
    Enumeration for reasoning modes in chat completions.

    This enumeration defines the various levels of reasoning effort that can be applied
    during chat completion generation. Higher reasoning modes allow the model to perform
    more thorough internal reasoning before responding, potentially improving response quality.
    """
    #: Low reasoning effort mode
    LOW = 'low'
    #: Medium reasoning effort mode
    MEDIUM = 'medium'
    #: High reasoning effort mode
    HIGH = 'high'

    @classmethod
    def _coerce(cls, value: ChatReasoningModeType) -> Self:
        if isinstance(value, cls):
            return value

        assert isinstance(value, str)
        return cls(value.lower())


ChatReasoningModeType = Union[
    Literal['low', 'medium', 'high'],
    Literal['LOW', 'MEDIUM', 'HIGH'],
    ChatReasoningMode,
]

@dataclass(frozen=True)
class ChatModelConfig(GPTModelConfig):
    """
    Configuration settings for chat completion models.

    This dataclass holds all configuration parameters for chat models,
    including generation parameters, reasoning settings, tool usage configuration,
    and additional query parameters.
    """

    #: The reasoning mode to apply during generation
    reasoning_mode: ChatReasoningMode | None = None
    #: Tools available for the model to use during completion
    tools: tuple[CompletionTool, ...] | None = None
    #: Extra arbitrary model query arguments
    extra_query: QueryType | None = None

    def _replace(self, **kwargs: Any) -> Self:
        if reasoning_mode := kwargs.get('reasoning_mode'):
            kwargs['reasoning_mode'] = ChatReasoningMode._coerce(reasoning_mode)

        if tools := kwargs.get('tools'):
            kwargs['tools'] = coerce_tuple(tools, BaseTool)  # type: ignore[type-abstract]

        extra_query: QueryType | None
        if extra_query := kwargs.get('extra_query'):
            assert isinstance(extra_query, dict)
            kwargs['extra_query'] = deepcopy(extra_query)

        return super()._replace(**kwargs)
