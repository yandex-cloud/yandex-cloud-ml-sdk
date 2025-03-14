# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCall as ProtoAssistantToolCall
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCallList as ProtoAssistantToolCallList
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCall as ProtoCompletionsToolCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCallList as ProtoCompletionsToolCallList

from yandex_cloud_ml_sdk._types.proto import ProtoBased


def tool_calls_from_proto(
    proto_list: ProtoAssistantToolCallList | ProtoCompletionsToolCallList,
    **_,
) -> tuple[ToolCall, ...]:
    return tuple(ToolCall._from_proto(proto=proto, **_) for proto in proto_list.tool_calls)


@dataclass(frozen=True)
class ToolCall(ProtoBased):
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoAssistantToolCall | ProtoCompletionsToolCall,
        **_,
    ) -> Self:
        return cls()
