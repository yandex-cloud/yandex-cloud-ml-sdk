from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .model import AsyncTextEmbeddingsModel, TextEmbeddingsModel


class BaseTextEmbeddings(BaseModelFunction[ModelTypeT]):
    """
    A class for text embeddings models.

    It provides the functionality to call a text embeddings model
    either by a well-known name or a full URI.
    """
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
        """
        Call the specified model for text embeddings.
        It returns an instance of the specified type of the model.

        This method constructs the URI for the model based on the provided
        name and version. If the name contains ``://``, it is
        treated as a full URI. Otherwise, it looks up the model name in
        the well-known names dictionary. But after this, in any case,
        we construct a URI in the form ``emb://<folder_id>/<model>/<version>``.

        :param model_name: the name or URI of the model to call.
        :param model_version: the version of the model to use.
            Defaults to 'latest'.
        """
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

@doc_from(BaseTextEmbeddings)
class TextEmbeddings(BaseTextEmbeddings):
    _model_type = TextEmbeddingsModel

@doc_from(BaseTextEmbeddings)
class AsyncTextEmbeddings(BaseTextEmbeddings):
    _model_type = AsyncTextEmbeddingsModel
