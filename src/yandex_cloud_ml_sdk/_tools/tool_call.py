# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Union

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCall as ProtoAssistantToolCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCall as ProtoCompletionsToolCall

from yandex_cloud_ml_sdk._types.json import JsonBased, JsonObject
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType

from .function_call import AsyncFunctionCall, FunctionCall, FunctionCallTypeT

ProtoToolCall = Union[ProtoAssistantToolCall, ProtoCompletionsToolCall]


# We need this class to separate _function_call_impl from dataclass
class FunctionCallMixin(Generic[FunctionCallTypeT]):
    _function_call_impl: type[FunctionCallTypeT]


@dataclass(frozen=True)
class BaseToolCall(
    JsonBased,
    ProtoBased[ProtoToolCall],
    FunctionCallMixin[FunctionCallTypeT]
):
    id: str | None
    function: FunctionCallTypeT | None
    _proto_origin: ProtoToolCall | None = field(repr=False)
    _json_origin: JsonObject | None = field(repr=False)

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoToolCall,
        sdk: SDKType,
    ) -> Self:
        function: FunctionCallTypeT | None = None
        if proto.HasField('function_call'):
            function = cls._function_call_impl._from_proto(proto=proto.function_call, sdk=sdk)
        return cls(
            id=None,
            function=function,
            _proto_origin=proto,
            _json_origin=None,
        )

    @classmethod
    def _from_json(cls, *, data: JsonObject, sdk: SDKType) -> Self:
        function: FunctionCallTypeT | None = None
        id_ = data.get('id')
        assert isinstance(id_, str)
        data['type'] = type_ = data.get('type') or 'function'
        if type_ == 'function':
            function_data = data.get('function', {})
            assert isinstance(function_data, dict)
            function = cls._function_call_impl._from_json(data=function_data, sdk=sdk)
        else:
            raise RuntimeError(f'got unknown tool_call type={type_}; try to upgrade sdk')

        return cls(
            id=id_,
            function=function,
            _proto_origin=None,
            _json_origin=data,
        )


class AsyncToolCall(BaseToolCall):
    _function_call_impl = AsyncFunctionCall


class ToolCall(BaseToolCall):
    _function_call_impl = FunctionCall


ToolCallTypeT = TypeVar('ToolCallTypeT', bound=BaseToolCall)


class HaveToolCalls(Generic[ToolCallTypeT]):
    pass
