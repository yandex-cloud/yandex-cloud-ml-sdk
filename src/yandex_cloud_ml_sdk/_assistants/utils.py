# pylint: disable=no-name-in-module
from __future__ import annotations

from yandex.cloud.ai.assistants.v1.common_pb2 import CompletionOptions, PromptTruncationOptions


def get_completion_options(
    *,
    temperature: float | None,
    max_tokens: int | None,
) -> CompletionOptions:
    options = CompletionOptions()
    if temperature is not None:
        options.temperature.value = temperature
    if max_tokens is not None:
        options.max_tokens.value = max_tokens

    return options


def get_prompt_trunctation_options(
    *,
    max_prompt_tokens: int | None
) -> PromptTruncationOptions:
    options = PromptTruncationOptions()
    if max_prompt_tokens is not None:
        options.max_prompt_tokens.value = max_prompt_tokens

    return options
