from __future__ import annotations

from typing import Optional, TypeVar, cast

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
# JsonObject needed for weird sphinx reasons
# pylint: disable=unused-import
from yandex_cloud_ml_sdk._types.schemas import JsonObject, ParametersType, schema_from_parameters  # noqa
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .tool import FunctionTool
from .tool_call import AsyncToolCall, HaveToolCalls, ToolCall, ToolCallTypeT


class BaseFunctionTools(BaseDomain, HaveToolCalls[ToolCallTypeT]):
    """
    Class for function tools.
    """
    _call_impl: type[ToolCallTypeT]

    def __call__(
        self,
        parameters: ParametersType,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        strict: UndefinedOr[bool] = UNDEFINED,
    ) -> FunctionTool:
        """
        Create a function tool with given parameters.

        :param parameters: Function parameters specification. Can be one of:
            - JSON Schema dict: A dictionary containing a valid JSON schema that describes the function parameters, their types, descriptions, and validation rules.
            - Pydantic BaseModel class: A class inheriting from pydantic.BaseModel. The JSON schema will be automatically generated from the model definition.
            - Pydantic dataclass: A dataclass decorated with @pydantic.dataclasses.dataclass. The JSON schema will be automatically generated from the dataclass definition.

        :param name: Optional function name. If not provided:
            - For JSON Schema dict: must be provided explicitly or error will be raised.
            - For Pydantic models: automatically inferred from the class __name__ attribute.

        :param description: Optional function description. If not provided:
            - For JSON Schema dict: taken from the 'description' field in the schema if present.
            - For Pydantic models: automatically inferred from the class docstring if present.

        :param strict: Whether to enforce strict parameter validation. When True, the function call will strictly validate that only the defined parameters are provided.
        """
        schema = schema_from_parameters(parameters)
        description_ = (
            get_defined_value(description, None) or
            cast(Optional[str], schema.get('description'))
        )
        name_ = (
            get_defined_value(name, None) or
            cast(Optional[str], schema.get('title'))
        )
        strict_: bool | None = get_defined_value(strict, None)

        if not name_:
            raise TypeError(
                f"sdk.{self._name}() missing keyword-only argument 'name' "
                "and failed to infer its value 'from parameters' argument"
            )

        return FunctionTool(
            parameters=schema,
            name=name_,
            description=description_,
            strict=strict_,
        )


@doc_from(BaseFunctionTools)
class AsyncFunctionTools(BaseFunctionTools[AsyncToolCall]):
    _call_impl = AsyncToolCall

@doc_from(BaseFunctionTools)
class FunctionTools(BaseFunctionTools[ToolCall]):
    _call_impl = ToolCall

#: Type variable representing any function tools type.
FunctionToolsTypeT = TypeVar('FunctionToolsTypeT', bound=BaseFunctionTools)
