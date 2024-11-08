# pylint: disable=no-name-in-module
from __future__ import annotations

from yandex.cloud.ai.assistants.v1.common_pb2 import CompletionOptions, PromptTruncationOptions

from yandex_cloud_ml_sdk._types.misc import UndefinedOr, is_defined


def get_completion_options(
    *,
    temperature: UndefinedOr[float] | None,
    max_tokens: UndefinedOr[int] | None,
) -> CompletionOptions:
    options = CompletionOptions()
    if temperature is not None and is_defined(temperature):
        options.temperature.value = temperature
    if max_tokens is not None and is_defined(max_tokens):
        options.max_tokens.value = max_tokens

    return options


def get_prompt_trunctation_options(
    *,
    max_prompt_tokens: UndefinedOr[int] | None
) -> PromptTruncationOptions:
    options = PromptTruncationOptions()
    if max_prompt_tokens is not None and is_defined(max_prompt_tokens):
        options.max_prompt_tokens.value = max_prompt_tokens

    return options
