# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Union

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCall as ProtoAssistantToolCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCall as ProtoCompletionsToolCall

from yandex_cloud_ml_sdk._types.proto import ProtoBased

from .function_call import AsyncFunctionCall, FunctionCall, FunctionCallTypeT

ProtoToolCall = Union[ProtoAssistantToolCall, ProtoCompletionsToolCall]


# We need this class to separate _function_call_impl from dataclass
class FunctionCallMixin(Generic[FunctionCallTypeT]):
    _function_call_impl: type[FunctionCallTypeT]


@dataclass(frozen=True)
class BaseToolCall(ProtoBased[ProtoToolCall], FunctionCallMixin[FunctionCallTypeT]):
    function: FunctionCallTypeT | None
    _proto_origin: ProtoToolCall = field(repr=False)

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoToolCall,
        sdk,
    ) -> Self:
        function: FunctionCallTypeT | None = None
        if proto.HasField('function_call'):
            function = cls._function_call_impl._from_proto(proto=proto.function_call, sdk=sdk)
        return cls(
            function=function,
            _proto_origin=proto,
        )


class AsyncToolCall(BaseToolCall):
    _function_call_impl = AsyncFunctionCall


class ToolCall(BaseToolCall):
    _function_call_impl = FunctionCall


ToolCallTypeT = TypeVar('ToolCallTypeT', bound=BaseToolCall)


class HaveToolCalls(Generic[ToolCallTypeT]):
    pass
