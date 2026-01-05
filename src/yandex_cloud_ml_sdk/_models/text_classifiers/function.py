from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT

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
    ) -> ModelTypeT:
        """Call the text classification model.

        Constructs the URI for the model based on the provided model's name
        and version. If the name contains ``://``, it is treated as a
        complete URI. Otherwise, it looks up the model name in
        the well-known names dictionary. But after this, in any case,
        we construct a URI in the form ``cls://<folder_id>/<model>/<version>``.

        :param model_name: the name or URI of the model to call.
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


class TextClassifiers(BaseTextClassifiers[TextClassifiersModel]):
    __doc__ = BaseTextClassifiers.__doc__

    _model_type = TextClassifiersModel


class AsyncTextClassifiers(BaseTextClassifiers[AsyncTextClassifiersModel]):
    __doc__ = BaseTextClassifiers.__doc__

    _model_type = AsyncTextClassifiersModel
