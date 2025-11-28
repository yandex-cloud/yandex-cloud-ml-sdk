from __future__ import annotations

from typing import Any, cast

from yandex_cloud_ml_sdk._chat.base_function import BaseChatFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .model import AsyncChatEmbeddingsModel, ChatEmbeddingsModel


class BaseChatEmbeddings(BaseChatFunction[ModelTypeT]):
    _prefix = 'emb://'


class ChatEmbeddings(BaseChatEmbeddings[ChatEmbeddingsModel]):
    _model_type = ChatEmbeddingsModel

    __list = run_sync(BaseChatEmbeddings[ChatEmbeddingsModel]._list)

    def list(
            self,
             *,
             timeout: float = 60,
             filters: dict[str, Any] | None = None
             ) -> tuple[ChatEmbeddingsModel, ...]:
        return cast(
            tuple[ChatEmbeddingsModel, ...],
            self.__list(timeout=timeout, filters=filters)
        )


class AsyncChatEmbeddings(BaseChatEmbeddings[AsyncChatEmbeddingsModel]):
    _model_type = AsyncChatEmbeddingsModel

    async def list(
            self,
            *,
            timeout: float = 60,
            filters: dict[str, Any] | None = None
            ) -> tuple[AsyncChatEmbeddingsModel, ...]:
        return await self._list(timeout=timeout, filters=filters)
