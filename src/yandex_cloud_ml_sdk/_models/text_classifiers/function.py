from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .model import AsyncTextClassifiersModel, TextClassifiersModel


class BaseTextClassifiers(BaseModelFunction[ModelTypeT]):
    """A class for text classifiers.

    It provides a common interface for text classification models and
    constructs the model URI based on the provided model name and version.
    """
    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ):
        """Call the text classification model.

        Constructs the URI for the model and initializes it
        and returns an instance of the model type initialized
        with the SDK and URI.

        :param model_name: the name of the model to be used.
        :param model_version: the version of the model to be used.
            Defaults to 'latest'.
        """
        if '://' in model_name:
            uri = model_name
        else:
            folder_id = self._sdk._folder_id
            uri = f'cls://{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )


@doc_from(BaseTextClassifiers)
class TextClassifiers(BaseTextClassifiers):
    _model_type = TextClassifiersModel

@doc_from(BaseTextClassifiers)
class AsyncTextClassifiers(BaseTextClassifiers):
    _model_type = AsyncTextClassifiersModel
