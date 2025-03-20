from __future__ import annotations

from typing import Optional, TypeVar, cast

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.schemas import ParametersType, schema_from_parameters

from .tool import FunctionTool
from .tool_call import AsyncToolCall, HaveToolCalls, ToolCall, ToolCallTypeT


class BaseFunctionTools(BaseDomain, HaveToolCalls[ToolCallTypeT]):
    _call_impl: type[ToolCallTypeT]

    def __call__(
        self,
        parameters: ParametersType,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
    ) -> FunctionTool:
        schema = schema_from_parameters(parameters)
        description_ = (
            get_defined_value(description, None) or
            cast(Optional[str], schema.get('description'))
        )
        name_ = (
            get_defined_value(name, None) or
            cast(Optional[str], schema.get('title'))
        )

        if not name_:
            raise TypeError(
                f"sdk.{self._name}() missing keyword-only argument 'name' "
                "and failed to infer its value 'from parameters' argument"
            )

        return FunctionTool(
            parameters=schema,
            name=name_,
            description=description_
        )


class AsyncFunctionTools(BaseFunctionTools[AsyncToolCall]):
    _call_impl = AsyncToolCall


class FunctionTools(BaseFunctionTools[ToolCall]):
    _call_impl = ToolCall


FunctionToolsTypeT = TypeVar('FunctionToolsTypeT', bound=BaseFunctionTools)
