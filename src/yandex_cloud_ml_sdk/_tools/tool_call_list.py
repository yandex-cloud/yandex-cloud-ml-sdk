# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, overload

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolCallList as ProtoAssistantToolCallList
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCallList as ProtoCompletionsToolCallList

from yandex_cloud_ml_sdk._types.json import JsonBased
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType

from .tool_call import ToolCallTypeT

ProtoToolCallListTypeT = TypeVar(
    'ProtoToolCallListTypeT',
    ProtoAssistantToolCallList,
    ProtoCompletionsToolCallList,
)


@dataclass
class BaseToolCallList(
    Sequence[ToolCallTypeT],
):
    tool_calls: tuple[ToolCallTypeT, ...]

    def __len__(self) -> int:
        return len(self.tool_calls)

    @overload
    def __getitem__(self, index: int, /) -> ToolCallTypeT:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[ToolCallTypeT, ...]:
        pass

    def __getitem__(self, index, /):
        return self.tool_calls[index]

    def __repr__(self):
        return f'{self.__class__.__name__}{self.tool_calls!r}'



@dataclass
class ToolCallList(
    BaseToolCallList[ToolCallTypeT],
    ProtoBased[ProtoToolCallListTypeT],
    Generic[ProtoToolCallListTypeT, ToolCallTypeT],
):
    _proto_origin: ProtoToolCallListTypeT = field(repr=False)

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoToolCallListTypeT,
        sdk: SDKType,
    ) -> Self:
        tool_call_impl = sdk.tools.function._call_impl  # pylint: disable=protected-access
        tool_calls = tuple(
            tool_call_impl._from_proto(proto=tool_call, sdk=sdk)
            for tool_call in proto.tool_calls
        )

        return cls(
            tool_calls=tool_calls,
            _proto_origin=proto,
        )


class HttpToolCallList(
    JsonBased,
    BaseToolCallList[ToolCallTypeT],
):
    @classmethod
    def _from_json(
        cls,
        *,
        data: dict[str, Any],
        sdk: SDKType,
    ) -> Self:
        tool_call_impl = sdk.tools.function._call_impl  # pylint: disable=protected-access

        tool_calls = tuple(
            tool_call_impl._from_json(data=tool_call, sdk=sdk)
            for tool_call in data
        )
        return cls(
            tool_calls=tool_calls,
        )
