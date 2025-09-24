# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .completions.function import AsyncChatCompletions, BaseChatCompletions, ChatCompletions


class BaseChat(DomainWithFunctions):
    """
    A class for Chat API domain operations.

    This class provides functionality for working with the
    `Yandex Cloud OpenAI Compatible API <https://yandex.cloud/docs/ai-studio/concepts/openai-compatibility>`_.
    It serves as the foundation for chat operations.
    """

    #: Chat API subdomain for working with text-generation models
    completions: BaseChatCompletions


@doc_from(BaseChat)
class AsyncChat(BaseChat):
    completions: AsyncChatCompletions


@doc_from(BaseChat)
class Chat(BaseChat):
    completions: ChatCompletions
