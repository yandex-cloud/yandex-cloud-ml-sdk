from __future__ import annotations

from typing import Literal, TypeVar, Union, cast

from typing_extensions import TypeAlias
# pylint: disable=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolChoice as ProtoCompletionsToolChoice

from yandex_cloud_ml_sdk._tools.tool import FunctionTool
from yandex_cloud_ml_sdk._types.json import JsonObject

from .function import FunctionDictType, validate_function_dict

ProtoToolChoice: TypeAlias = ProtoCompletionsToolChoice
ProtoToolChoiceTypeT = TypeVar('ProtoToolChoiceTypeT', bound=ProtoToolChoice)

ToolChoiceStringType: TypeAlias = Literal[
    'none', 'None', 'NONE',
    'auto', 'Auto', 'AUTO',
    'required', 'Required', 'REQUIRED'
]

ToolChoiceType: TypeAlias = Union[ToolChoiceStringType, FunctionDictType, FunctionTool]


STRING_TOOL_CHOICES = ('NONE', 'AUTO', 'REQUIRED')


def coerce_to_proto(
    tool_choice: ToolChoiceType, expected_type: type[ProtoToolChoiceTypeT]
) -> ProtoToolChoiceTypeT:
    if isinstance(tool_choice, str):
        tool_choice = cast(ToolChoiceStringType, tool_choice.upper())
        if tool_choice not in STRING_TOOL_CHOICES:
            raise ValueError(f'wrong {tool_choice=}, use one of {STRING_TOOL_CHOICES}')

        tool_choice_value = expected_type.ToolChoiceMode.Value(tool_choice)

        return expected_type(mode=tool_choice_value)

    if isinstance(tool_choice, dict):
        tool_choice = validate_function_dict(tool_choice)
        return expected_type(function_name=tool_choice['function']['name'])

    if isinstance(tool_choice, FunctionTool):
        return expected_type(function_name=tool_choice.name)

    raise TypeError(f'wrong {type(tool_choice)=}, expected string or dict')


def coerce_to_json(tool_choice: ToolChoiceType) -> JsonObject | str | FunctionDictType:
    if isinstance(tool_choice, str):
        return tool_choice

    if isinstance(tool_choice, dict):
        tool_choice = validate_function_dict(tool_choice)
        return tool_choice

    if isinstance(tool_choice, FunctionTool):
        return {
            'type': 'function',
            'function': {
                'name': tool_choice.name,
            }
        }

    raise TypeError(f'wrong {type(tool_choice)=}, expected string or dict')
