# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions

from .completions.function import AsyncChatCompletions, BaseChatCompletions, ChatCompletions


class BaseChat(DomainWithFunctions):
    completions: BaseChatCompletions


class AsyncChat(BaseChat):
    completions: AsyncChatCompletions


class Chat(BaseChat):
    completions: ChatCompletions
