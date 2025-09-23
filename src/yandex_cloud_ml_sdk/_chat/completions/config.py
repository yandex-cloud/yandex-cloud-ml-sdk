from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Union

from typing_extensions import Self, TypeAlias

from yandex_cloud_ml_sdk._models.completions.config import CompletionTool, GPTModelConfig
from yandex_cloud_ml_sdk._tools.tool import BaseTool
from yandex_cloud_ml_sdk._types.schemas import JsonObject
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


class ChatReasoningMode(str, Enum):
    """Enumeration for reasoning modes.

    This class defines the various modes of reasoning that can be used
    in the ``sdk.chat.completions`` model's configurations.
    """

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

    @classmethod
    def _coerce(cls, value: ChatReasoningModeType) -> Self:
        if isinstance(value, cls):
            return value

        assert isinstance(value, str)
        return cls(value.lower())


#: type alias for reasoning mode representation
ChatReasoningModeType = Union[
    Literal['low', 'medium', 'high'],
    Literal['LOW', 'MEDIUM', 'HIGH'],
    ChatReasoningMode
]
#: type alias for model arguments
QueryType: TypeAlias = JsonObject


@dataclass(frozen=True)
class ChatModelConfig(GPTModelConfig):
    """Configuration for the chat model.

    It holds the configuration settings for the chat model,
    including parameters for generation and tool usage.
    """

    reasoning_mode: ChatReasoningMode | None = None
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
