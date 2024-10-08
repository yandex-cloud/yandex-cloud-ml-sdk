from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT

from .model import AsyncTextEmbeddingsModel, TextEmbeddingsModel


class BaseTextEmbeddings(BaseModelFunction[ModelTypeT]):
    _well_known_names = {
        'doc': 'text-search-doc',
        'query': 'text-search-query',
    }

    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ):
        if '://' in model_name:
            uri = model_name
        else:
            model_name = self._well_known_names.get(model_name, model_name)
            folder_id = self._sdk._folder_id
            uri = f'emb://{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )


class TextEmbeddings(BaseTextEmbeddings):
    _model_type = TextEmbeddingsModel


class AsyncTextEmbeddings(BaseTextEmbeddings):
    _model_type = AsyncTextEmbeddingsModel
