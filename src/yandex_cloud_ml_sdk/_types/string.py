from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from typing_extensions import TypeAlias

#: Type alias for values that can be either a single string or a sequence of strings
SmartStringSequence: TypeAlias = Union[str, Sequence[str]]


def coerce_string_sequence(value: SmartStringSequence) -> tuple[str, ...]:
    """
    Convert a SmartStringSequence to a tuple of strings.

    This function normalizes input that can be either a single string
    or a sequence of strings into a consistent tuple format.

    :param value: Input value that can be either a string or sequence of strings
    """
    if isinstance(value, str):
        return (value, )

    return tuple(value)
