from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from typing_extensions import TypeAlias

#: Type alias for values that can be either a single string or a sequence of strings
SmartStringSequence: TypeAlias = Union[str, Sequence[str]]


def coerce_string_sequence(value: SmartStringSequence) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value, )

    return tuple(value)
