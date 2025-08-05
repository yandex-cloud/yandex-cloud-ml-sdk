# pylint: disable=no-name-in-module
from __future__ import annotations

from yandex.cloud.ai.assistants.v1.common_pb2 import CompletionOptions

from yandex_cloud_ml_sdk._types.misc import UndefinedOr, is_defined


def get_completion_options(
    *,
    temperature: UndefinedOr[float] | None,
    max_tokens: UndefinedOr[int] | None,
) -> CompletionOptions | None:
    """Create a CompletionOptions object from temperature and max_tokens parameters.

    This utility function constructs a CompletionOptions protobuf object based on
    the provided temperature and max_tokens parameters. If both parameters are
    undefined or None, the function returns None to indicate no options should
    be applied.

    Args:
        temperature: The temperature parameter for text generation. Controls the
            randomness of the model's output. Higher values (e.g., 0.8) make the
            output more random, while lower values (e.g., 0.2) make it more
            deterministic. Can be None or an undefined value.
        max_tokens: The maximum number of tokens to generate in the response.
            Limits the length of the generated text. Can be None or an undefined
            value.

    Returns:
        CompletionOptions: A protobuf object containing the specified completion
            options, or None if no valid options were provided (both parameters
            are None or undefined).
    """
    options = CompletionOptions()
    empty = True
    if temperature is not None and is_defined(temperature):
        empty = False
        options.temperature.value = temperature
    if max_tokens is not None and is_defined(max_tokens):
        empty = False
        options.max_tokens.value = max_tokens

    if empty:
        return None

    return options
