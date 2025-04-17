# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence, overload

from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Alternative as ProtoAlternative
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ContentUsage as ProtoUsage
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import CompletionResponse

from yandex_cloud_ml_sdk._tools.tool_call import HaveToolCalls, ToolCallTypeT
from yandex_cloud_ml_sdk._tools.tool_call_list import ProtoCompletionsToolCallList, ToolCallList
from yandex_cloud_ml_sdk._types.message import TextMessage
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._types.result import BaseResult


@dataclass(frozen=True)
class Usage:
    input_text_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CompletionUsage(Usage, ProtoBased[ProtoUsage]):
    reasoning_tokens: int

    @classmethod
    def _from_proto(cls, *, proto: ProtoUsage, **_) -> CompletionUsage:
        return cls(
            input_text_tokens=proto.input_text_tokens,
            completion_tokens=proto.completion_tokens,
            total_tokens=proto.total_tokens,
            reasoning_tokens=proto.completion_tokens_details.reasoning_tokens
        )


_s = ProtoAlternative

class AlternativeStatus(int, Enum):
    UNSPECIFIED = _s.ALTERNATIVE_STATUS_UNSPECIFIED
    PARTIAL = _s.ALTERNATIVE_STATUS_PARTIAL
    TRUNCATED_FINAL = _s.ALTERNATIVE_STATUS_TRUNCATED_FINAL
    FINAL = _s.ALTERNATIVE_STATUS_FINAL
    CONTENT_FILTER = _s.ALTERNATIVE_STATUS_CONTENT_FILTER
    TOOL_CALLS = _s.ALTERNATIVE_STATUS_TOOL_CALLS

    UNKNOWN = -1

    @classmethod
    def _from_proto(cls, status: int):
        try:
            return cls(status)
        except ValueError:
            return cls(-1)


@dataclass(frozen=True)
class Alternative(TextMessage, ProtoBased[ProtoAlternative], HaveToolCalls[ToolCallTypeT]):
    status: AlternativeStatus
    tool_calls: ToolCallList[ProtoCompletionsToolCallList, ToolCallTypeT] | None

    @classmethod
    def _from_proto(cls, *, proto: ProtoAlternative, sdk: SDKType) -> Alternative:
        message = proto.message

        # pylint: disable=protected-access
        tool_call_impl: type[ToolCallTypeT] = sdk.tools.function._call_impl

        tool_call_list: ToolCallList | None = None
        if message.tool_call_list.tool_calls:
            tool_call_list = ToolCallList._from_proto(
                proto=message.tool_call_list,
                sdk=sdk,
                tool_call_impl=tool_call_impl
            )

        return cls(
            role=message.role,
            text=message.text,
            status=AlternativeStatus._from_proto(proto.status),
            tool_calls=tool_call_list,
        )


@dataclass(frozen=True)
class GPTModelResult(BaseResult[CompletionResponse], Sequence, HaveToolCalls[ToolCallTypeT]):
    alternatives: tuple[Alternative[ToolCallTypeT], ...]
    usage: CompletionUsage
    model_version: str

    @classmethod
    def _from_proto(cls, *, proto: CompletionResponse, sdk: SDKType) -> GPTModelResult:
        alternatives = tuple(Alternative._from_proto(proto=alternative, sdk=sdk) for alternative in proto.alternatives)
        usage = CompletionUsage._from_proto(proto=proto.usage, sdk=sdk)

        return cls(
            alternatives=alternatives,
            usage=usage,
            model_version=proto.model_version,
        )

    def __len__(self):
        return len(self.alternatives)

    @overload
    def __getitem__(self, index: int, /) -> Alternative:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[Alternative, ...]:
        pass

    def __getitem__(self, index, /):
        return self.alternatives[index]

    @property
    def role(self) -> str:
        return self[0].role

    @property
    def text(self) -> str:
        return self[0].text

    @property
    def status(self) -> AlternativeStatus:
        return self[0].status

    @property
    def tool_calls(self) -> ToolCallList[ProtoCompletionsToolCallList, ToolCallTypeT] | None:
        return self[0].tool_calls
