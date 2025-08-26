from __future__ import annotations

from typing import cast

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .model import AsyncChatModel, ChatModel


class BaseChatCompletions(BaseModelFunction[ModelTypeT]):
    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ) -> ModelTypeT:
        if '://' in model_name:
            uri = model_name
        else:
            folder_id = self._sdk._folder_id
            uri = f'gpt://{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )

    async def _list(self, *, timeout) -> tuple[ModelTypeT, ...]:
        async with self._sdk._client.httpx_for_service('http_completions', timeout) as client:
            response = await client.get(
                '/models',
                headers={
                    'OpenAI-Project': self._sdk._folder_id
                },
                timeout=timeout,
            )

        response.raise_for_status()

        raw_models = response.json()['data']
        return tuple(
            self._model_type(sdk=self._sdk, uri=raw_model['id'])
            for raw_model in raw_models
            if raw_model['id'].startswith('gpt://')
        )


class ChatCompletions(BaseChatCompletions[ChatModel]):
    _model_type = ChatModel

    __list = run_sync(BaseChatCompletions[ChatModel]._list)

    def list(self, *, timeout: float = 60) -> tuple[ChatModel, ...]:
        return cast(
            tuple[ChatModel, ...],
            self.__list(timeout=timeout)
        )


class AsyncChatCompletions(BaseChatCompletions[AsyncChatModel]):
    __doc__ = BaseChatCompletions.__doc__

    _model_type = AsyncChatModel

    async def list(self, *, timeout: float = 60) -> tuple[AsyncChatModel, ...]:
        return await self._list(timeout=timeout)
