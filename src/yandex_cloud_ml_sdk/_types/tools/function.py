from __future__ import annotations

from typing import Any, Literal, TypedDict, cast

from typing_extensions import NotRequired


class FunctionNameType(TypedDict):
    """
    Type definition for function name and optional instruction.

    This TypedDict defines the structure for a function specification
    containing a required name and an optional instruction field.
    """
    name: str
    instruction: NotRequired[str]


class FunctionDictType(TypedDict):
    """
    Type definition for a complete function dictionary structure.

    This TypedDict defines the complete structure for a function tool,
    containing a type field set to 'function' and a function specification.
    """
    type: Literal['function']
    function: FunctionNameType


def validate_function_dict(function: Any) -> FunctionDictType:
    """
    Validate and cast a dictionary to FunctionDictType.

    Validates that the provided dictionary conforms to the expected structure
    for a function tool definition and returns it as a properly typed FunctionDictType.
    """
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
