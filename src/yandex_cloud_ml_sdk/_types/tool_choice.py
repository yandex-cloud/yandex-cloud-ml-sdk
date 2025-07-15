from __future__ import annotations

from typing import Literal, TypedDict, TypeVar, Union, cast

from typing_extensions import TypeAlias
# pylint: disable=no-name-in-module
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolChoice as ProtoCompletionsToolChoice

from yandex_cloud_ml_sdk._tools.tool import FunctionTool

ProtoToolChoice: TypeAlias = ProtoCompletionsToolChoice
ProtoToolChoiceTypeT = TypeVar('ProtoToolChoiceTypeT', bound=ProtoToolChoice)


class FunctionNameType(TypedDict):
    name: str


class ToolChoiceDictType(TypedDict):
    type: Literal['function']
    function: FunctionNameType


ToolChoiceStringType: TypeAlias = Literal[
    'none', 'None', 'NONE',
    'auto', 'Auto', 'AUTO',
    'required', 'Required', 'REQUIRED'
]

ToolChoiceType: TypeAlias = Union[ToolChoiceStringType, ToolChoiceDictType, FunctionTool]

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
        if (
            tool_choice.get('type') != 'function' or
            not isinstance(tool_choice.get('function'), dict) or
            not isinstance(tool_choice['function'].get('name'), str)
        ):
            raise ValueError(
                'wrong dict structure for tool_choice, expected '
                '`{"type": "function", "function": {"name": function_name}}`, '
                'got {tool_choice}'
            )

        tool_choice = cast(ToolChoiceDictType, tool_choice)

        return expected_type(function_name=tool_choice['function']['name'])

    if isinstance(tool_choice, FunctionTool):
        return expected_type(function_name=tool_choice.name)

    raise TypeError(f'wrong {type(tool_choice)=}, expected string or dict')
