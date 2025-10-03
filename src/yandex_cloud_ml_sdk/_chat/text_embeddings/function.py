from __future__ import annotations

from typing import cast

from yandex_cloud_ml_sdk._chat.base_function import BaseChatFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .model import AsyncChatEmbeddingsModel, ChatEmbeddingsModel


class BaseChatEmbeddings(BaseChatFunction[ModelTypeT]):
    _prefix = 'emb://'


class ChatEmbeddings(BaseChatEmbeddings[ChatEmbeddingsModel]):
    _model_type = ChatEmbeddingsModel

    __list = run_sync(BaseChatEmbeddings[ChatEmbeddingsModel]._list)

    def list(self, *, timeout: float = 60) -> tuple[ChatEmbeddingsModel, ...]:
        return cast(
            tuple[ChatEmbeddingsModel, ...],
            self.__list(timeout=timeout)
        )


class AsyncChatEmbeddings(BaseChatEmbeddings[AsyncChatEmbeddingsModel]):
    _model_type = AsyncChatEmbeddingsModel

    async def list(self, *, timeout: float = 60) -> tuple[AsyncChatEmbeddingsModel, ...]:
        return await self._list(timeout=timeout)
