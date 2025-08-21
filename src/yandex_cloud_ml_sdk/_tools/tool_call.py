# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Union

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCall as ProtoAssistantToolCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCall as ProtoCompletionsToolCall

from yandex_cloud_ml_sdk._types.json import JsonBased, JsonObject
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .function_call import AsyncFunctionCall, FunctionCall, FunctionCallTypeT

ProtoToolCall = Union[ProtoAssistantToolCall, ProtoCompletionsToolCall]


# We need this class to separate _function_call_impl from dataclass
class FunctionCallMixin(Generic[FunctionCallTypeT]):
    """
    Mixin class providing function call implementation type.
    """
    _function_call_impl: type[FunctionCallTypeT]


@dataclass(frozen=True)
class BaseToolCall(
    JsonBased,
    ProtoBased[ProtoToolCall],
    FunctionCallMixin[FunctionCallTypeT]
):
    """
    Base class representing a tool call in Yandex Cloud ML SDK.
    """
    #: Unique tool call identifier
    id: str | None
    #: Function call associated with this tool call
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
        """
        Create BaseToolCall instance from protobuf message.

        :param proto: Protobuf message to convert
        :param sdk: SDK instance
        """
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
        if data.get('type') == 'function':
            function_data = data.get('function', {})
            assert isinstance(function_data, dict)
            function = cls._function_call_impl._from_json(data=function_data, sdk=sdk)

        return cls(
            id=id_,
            function=function,
            _proto_origin=None,
            _json_origin=data,
        )

@doc_from(BaseToolCall)
class AsyncToolCall(BaseToolCall):
    _function_call_impl = AsyncFunctionCall

@doc_from(BaseToolCall)
class ToolCall(BaseToolCall):
    _function_call_impl = FunctionCall


ToolCallTypeT = TypeVar('ToolCallTypeT', bound=BaseToolCall)
"""
Type variable representing any tool call type.
"""


class HaveToolCalls(Generic[ToolCallTypeT]):
   """
   Interface for objects that can have tool calls.
   """
