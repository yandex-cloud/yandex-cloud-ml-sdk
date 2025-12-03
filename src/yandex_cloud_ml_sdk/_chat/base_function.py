from __future__ import annotations

from typing import Any

from typing_extensions import override

from yandex_cloud_ml_sdk._chat.utils import ModelFilter, model_match
from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT

class BaseChatFunction(BaseModelFunction[ModelTypeT]):
    _prefix: str

    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ) -> ModelTypeT:
        """
        Create a model instance in selected chat subdomain (completions, embeddings, etc)

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
            uri = f'{self._prefix}{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )
    async def _fetch_raw_models(self, timeout: float) -> list[dict[str, Any]]:
        """
        Returns raw data for all available models in selected subdomain.
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
        return response.json()['data']

    async def _list(
        self,
        *,
        timeout,
        filters: ModelFilter | None
    ) -> tuple[ModelTypeT, ...]:
        """
        Returns all available models in selected subdomain (completions, embeddings, etc)

        :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
        :param filters: Optional dict with filters, where keys are model attribute names and values are the desired values.

        >>> filters = {'owner': 'alice', 'version': 'v2', 'fine_tuned': True}

        """

        raw_models = await self._fetch_raw_models(timeout)

        models = (
            self._model_type(sdk=self._sdk, uri=raw_model['id'], owner=raw_model['owned_by'])
            for raw_model in raw_models
            if raw_model['id'].startswith(self._prefix)
        )

        return tuple(
            model for model in models if model_match(model, filters)
        )
