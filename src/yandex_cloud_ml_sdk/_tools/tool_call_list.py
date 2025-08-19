# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar, overload

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCallList as ProtoAssistantToolCallList
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCallList as ProtoCompletionsToolCallList

from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType

from .tool_call import ToolCallTypeT

ProtoToolCallListTypeT = TypeVar('ProtoToolCallListTypeT', ProtoAssistantToolCallList, ProtoCompletionsToolCallList)
"""
Type variable representing protobuf tool call list types.
"""


@dataclass
class ToolCallList(
    Sequence[ToolCallTypeT],
    ProtoBased[ProtoToolCallListTypeT],
    Generic[ProtoToolCallListTypeT, ToolCallTypeT],
):
    """
    List of tool calls in Yandex Cloud ML SDK.
    """
    _proto_origin: ProtoToolCallListTypeT
    #: Tuple of tool calls
    tool_calls: tuple[ToolCallTypeT, ...]

    def __len__(self) -> int:
        """
        Return number of tool calls in the list.
        """
        return len(self.tool_calls)

    @overload
    def __getitem__(self, index: int, /) -> ToolCallTypeT:
        """
        Get tool call by integer index.
        
        :param index: Index of tool call to get
        """
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[ToolCallTypeT, ...]:
        """
        Get slice of tool calls.
        
        :param slice_: Slice to get
        """
        pass

    def __getitem__(self, index, /):
        """
        Get tool call(s) by index or slice.
        
        :param index: Index or slice to get
        """
        return self.tool_calls[index]

    def __repr__(self):
        """
        Return string representation of tool call list.
        """
        return f'{self.__class__.__name__}{self.tool_calls!r}'

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoToolCallListTypeT,
        sdk: SDKType,
        tool_call_impl: type[ToolCallTypeT] | None = None,
    ) -> Self:
        """
        Create ToolCallList from protobuf message.
        
        :param proto: Protobuf message to convert
        :param sdk: SDK instance
        :param tool_call_impl: Tool call implementation class
        """
        # I know for sure it will be called only with tool_call_impl
        assert tool_call_impl
        tool_calls = tuple(
            tool_call_impl._from_proto(proto=tool_call, sdk=sdk)
            for tool_call in proto.tool_calls
        )

        return cls(
            tool_calls=tool_calls,
            _proto_origin=proto,
        )
