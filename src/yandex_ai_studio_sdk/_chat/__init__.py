# pylint: disable=protected-access
from __future__ import annotations

from yandex_ai_studio_sdk._types.domain import DomainWithFunctions
from yandex_ai_studio_sdk._utils.doc import doc_from

from .completions.function import AsyncChatCompletions, BaseChatCompletions, ChatCompletions
from .text_embeddings.function import AsyncChatEmbeddings, BaseChatEmbeddings, ChatEmbeddings


class BaseChat(DomainWithFunctions):
    """
    A class for Chat API domain operations.

    This class provides functionality for working with the
    `Yandex Cloud OpenAI Compatible API_BaseChat_URL <https://yandex.cloud/docs/ai-studio/concepts/openai-compatibility>`_.
    It serves as the foundation for chat operations.
    """

    #: Chat API subdomain for working with text-generation models
    completions: BaseChatCompletions
    text_embeddings: BaseChatEmbeddings


@doc_from(BaseChat)
class AsyncChat(BaseChat):
    completions: AsyncChatCompletions
    text_embeddings: AsyncChatEmbeddings


@doc_from(BaseChat)
class Chat(BaseChat):
    completions: ChatCompletions
    text_embeddings: ChatEmbeddings
