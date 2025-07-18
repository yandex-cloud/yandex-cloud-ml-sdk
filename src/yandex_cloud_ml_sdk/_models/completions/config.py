from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Union

from typing_extensions import TypeAlias
# pylint: disable=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ReasoningOptions as ProtoReasoningOptions

from yandex_cloud_ml_sdk._tools.tool import FunctionTool
from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig
from yandex_cloud_ml_sdk._types.schemas import ResponseType
from yandex_cloud_ml_sdk._types.tools.tool_choice import ToolChoiceType
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase

_m = ProtoReasoningOptions.ReasoningMode


class ReasoningMode(ProtoEnumBase, Enum):
    """Enumeration for reasoning modes.

    This class defines the various modes of reasoning that can be used
    in the model's configurations.
    """
    #: indicates that the reasoning mode is unspecified
    REASONING_MODE_UNSPECIFIED = _m.REASONING_MODE_UNSPECIFIED
    #: indicates that reasoning is disabled
    DISABLED = _m.DISABLED
    #: indicates that reasoning is enabled but hidden
    ENABLED_HIDDEN = _m.ENABLED_HIDDEN

#: type alias for reasoning mode representation
ReasoningModeType = Union[int, str, ReasoningMode]
#: type alias for completion tools
CompletionTool: TypeAlias = FunctionTool


@dataclass(frozen=True)
class GPTModelConfig(BaseModelConfig):
    """Configuration for the GPT model.

    It holds the configuration settings for the GPT model,
    including parameters for generation and tool usage.
    """
    #: a sampling temperature to use - higher values mean more random results; should be a double number between 0 (inclusive) and 1 (inclusive)
    temperature: float | None = None
    #: a maximum number of tokens to generate in the response
    max_tokens: int | None = None
    #: the mode of reasoning to apply during generation, allowing the model to perform internal reasoning before responding
    reasoning_mode: ReasoningModeType | None = None
    #: a format of the response returned by the model. Could be a JsonSchema, a JSON string, or a pydantic model
    response_format: ResponseType | None = None
    #: tools to use for completion. Can be a sequence or a single tool
    tools: Sequence[CompletionTool] | CompletionTool | None = None
    #: whether to allow parallel calls to tools during completion; defaults to 'true'
    parallel_tool_calls: bool | None = None
    #: the strategy for choosing tools: depending on this parameter, the model can always call some tool, call the specific tool or don't call any tool.
    tool_choice: ToolChoiceType | None = None
