# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict, TypeVar, Union, cast

from typing_extensions import NotRequired, Required, TypeAlias
from yandex.cloud.ai.assistants.v1.common_pb2 import FunctionResult as ProtoAssistantFunctionResult
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolResult as ProtoAssistantToolResult
from yandex.cloud.ai.assistants.v1.common_pb2 import ToolResultList as ProtoAssistantToolResultList
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import FunctionResult as ProtoCompletionsFunctionResult
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolResult as ProtoCompletionsToolResult
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolResultList as ProtoCompletionsToolResultList

from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple

ProtoToolResultListTypeT = TypeVar(
    'ProtoToolResultListTypeT',
    ProtoAssistantToolResultList,
    ProtoCompletionsToolResultList
)
ProtoToolResultTypeT = TypeVar(
    'ProtoToolResultTypeT',
    ProtoAssistantToolResult,
    ProtoCompletionsToolResult,
)
ProtoToolResultType = Union[ProtoAssistantToolResult, ProtoCompletionsToolResult]
ProtoFunctionResultType = Union[ProtoAssistantFunctionResult, ProtoCompletionsFunctionResult]


class FunctionResultDict(TypedDict):
    name: Required[str]
    content: Required[str]
    type: NotRequired[str]


FunctionResultType: TypeAlias = FunctionResultDict
ToolResultType: TypeAlias = FunctionResultType
ToolResultDictType: TypeAlias = FunctionResultDict
ToolResultInputType: TypeAlias = Union[ToolResultType, Iterable[ToolResultType]]


def tool_result_to_proto(
    tool_result: ToolResultType,
    proto_type: type[ProtoToolResultTypeT]
) -> ProtoToolResultTypeT:
    proto_function_result_type = cast(type[ProtoFunctionResultType], {
        ProtoAssistantToolResult: ProtoAssistantFunctionResult,
        ProtoCompletionsToolResult: ProtoCompletionsFunctionResult,
    }[proto_type])

    proto_function_result: ProtoFunctionResultType | None = None

    if isinstance(tool_result, dict):
        result_type_str = tool_result.get('type', 'function')

        if result_type_str == 'function':
            if 'name' not in tool_result or 'content' not in tool_result:
                raise TypeError("tool result for function call need to have 'name' and 'content' fields")

            proto_function_result = proto_function_result_type(
                name=tool_result['name'],
                content=tool_result['content']
            )
        else:
            raise TypeError('only tool results with type="function" are supported in current SDK version')
    else:
        raise TypeError('only dict format supported at the moment')

    return proto_type(
        function_result=proto_function_result  # type: ignore[arg-type]
    )


def tool_results_to_proto(
    tool_results: ToolResultInputType,
    proto_type: type[ProtoToolResultListTypeT]
) -> ProtoToolResultListTypeT:
    proto_tool_result_type = cast(type[ProtoToolResultType], {
        ProtoAssistantToolResultList: ProtoAssistantToolResult,
        ProtoCompletionsToolResultList: ProtoCompletionsToolResult,
    }[proto_type])

    tool_results = coerce_tuple(tool_results, cast(type[FunctionResultDict], dict))

    proto_tool_results: list[object] = []
    for tool_result in tool_results:
        proto_tool_result: ProtoToolResultType = tool_result_to_proto(  # type: ignore[assignment]
            tool_result,
            proto_tool_result_type  # type: ignore[type-var]
        )
        proto_tool_results.append(proto_tool_result)

    return proto_type(
        tool_results=proto_tool_results  # type: ignore[arg-type]
    )
