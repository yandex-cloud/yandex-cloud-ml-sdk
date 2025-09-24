# pylint: disable=protected-access
from __future__ import annotations

from typing import cast

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .model import AsyncChatModel, ChatModel


class BaseChatCompletions(BaseModelFunction[ModelTypeT]):
    """
    A class for working with chat completions models.

    This class provides the core functionality for creating chat model instances
    and managing completions. It handles model URI construction and provides
    methods for listing available models.
    """

    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ) -> ModelTypeT:
        """
        Create a chat model instance for generating completions.

        Constructs the model URI based on the provided name and version.
        If the name contains '://', it is treated as a full URI.
        Otherwise constructs a URI in the form 'gpt://<folder_id>/<model>/<version>'.

        :param model_name: The name or URI of the model.
        :param model_version: The version of the model to use.
            Defaults to 'latest'.
        """

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
        """Returns all available chat models.

        :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
        """

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


@doc_from(BaseChatCompletions)
class ChatCompletions(BaseChatCompletions[ChatModel]):
    _model_type = ChatModel

    __list = run_sync(BaseChatCompletions[ChatModel]._list)

    @doc_from(BaseChatCompletions._list)
    def list(self, *, timeout: float = 60) -> tuple[ChatModel, ...]:
        return cast(
            tuple[ChatModel, ...],
            self.__list(timeout=timeout)
        )


@doc_from(BaseChatCompletions)
class AsyncChatCompletions(BaseChatCompletions[AsyncChatModel]):
    _model_type = AsyncChatModel

    @doc_from(BaseChatCompletions._list)
    async def list(self, *, timeout: float = 60) -> tuple[AsyncChatModel, ...]:
        return await self._list(timeout=timeout)
