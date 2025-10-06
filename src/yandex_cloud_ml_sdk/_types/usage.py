# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseUsage:
    """A class representing usage statistics for some request."""

    #: the number of tokens in the input text
    input_text_tokens: int
    #: the total number of tokens used
    total_tokens: int
