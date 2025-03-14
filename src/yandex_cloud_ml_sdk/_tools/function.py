from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar, cast

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.schemas import ParametersType, schema_from_parameters

from .tool import FunctionTool
from .tool_call import AsyncToolCall, HaveToolCalls, ProtoToolCall, ToolCall, ToolCallTypeT


class BaseFunctionTools(BaseDomain, HaveToolCalls[ToolCallTypeT]):
    _call_impl: type[ToolCallTypeT]

    def __call__(
        self,
        *,
        name: str,
        description: UndefinedOr[str] = UNDEFINED,
        parameters: ParametersType,
    ) -> FunctionTool:
        schema = schema_from_parameters(parameters)

        return FunctionTool(
            parameters=schema,
            name=name,
            description=get_defined_value(description, None)
        )

    def _tool_calls_from_proto(self, proto_list: Iterable[ProtoToolCall]) -> tuple[ToolCallTypeT, ...]:
        return tuple(
            cast(ToolCallTypeT, self._call_impl._from_proto(proto=proto, sdk=self._sdk))
            for proto in proto_list
        )


class AsyncFunctionTools(BaseFunctionTools[AsyncToolCall]):
    _call_impl = AsyncToolCall


class FunctionTools(BaseFunctionTools[ToolCall]):
    _call_impl = ToolCall


FunctionToolsTypeT = TypeVar('FunctionToolsTypeT', bound=BaseFunctionTools)
