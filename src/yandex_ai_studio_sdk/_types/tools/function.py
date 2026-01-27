from __future__ import annotations

from typing import Any, Literal, TypedDict, cast

from typing_extensions import NotRequired


class FunctionNameType(TypedDict):
    name: str
    instruction: NotRequired[str]


class FunctionDictType(TypedDict):
    type: Literal['function']
    function: FunctionNameType


def validate_function_dict(function: Any) -> FunctionDictType:
    if (
        function.get('type') != 'function' or
        not isinstance(function.get('function'), dict) or
        not isinstance(function['function'].get('name'), str) or
        not isinstance(function['function'].get('instruction', ''), str)
    ):
        raise ValueError(
            'wrong dict structure for function description, expected '
            '`{"type": "function", "function": {"name": str[, "instruction": str}}`, '
            f'got {function}'
        )

    return cast(FunctionDictType, function)
