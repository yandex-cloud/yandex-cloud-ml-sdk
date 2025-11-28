# pylint: disable=protected-access
from __future__ import annotations

from typing import Any, cast

from yandex_cloud_ml_sdk._chat.base_function import BaseChatFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .model import AsyncChatModel, ChatModel


class BaseChatCompletions(BaseChatFunction[ModelTypeT]):
    """
    A class for working with chat completions models.

    This class provides the core functionality for creating chat model instances
    and managing completions. It handles model URI construction and provides
    methods for listing available models.
    """

    _prefix = 'gpt://'


@doc_from(BaseChatCompletions)
class ChatCompletions(BaseChatCompletions[ChatModel]):
    _model_type = ChatModel

    __list = run_sync(BaseChatCompletions[ChatModel]._list)

    @doc_from(BaseChatCompletions._list)
    def list(
            self,
            *,
            timeout: float = 60,
            filters: dict[str, Any] | None = None
    ) -> tuple[ChatModel, ...]:
        return cast(
            tuple[ChatModel, ...],
            self.__list(timeout=timeout, filters=filters)
        )


@doc_from(BaseChatCompletions)
class AsyncChatCompletions(BaseChatCompletions[AsyncChatModel]):
    _model_type = AsyncChatModel

    @doc_from(BaseChatCompletions._list)
    async def list(
            self,
            *,
            timeout: float = 60,
            filters: dict[str, Any] | None = None
            ) -> tuple[AsyncChatModel, ...]:
        return await self._list(timeout=timeout, filters=filters)
