from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT

from .model import AsyncGPTModel, GPTModel


class BaseCompletions(BaseModelFunction[ModelTypeT]):
    """
    A class for handling completions models.

    It defines the core functionality for calling a model
    to generate completions based on the provided model name and version.
    """

    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ) -> ModelTypeT:
        """
        Create a model object to call for generating completions.

        This method constructs the URI for the model based on the provided
        name and version. If the name contains ``://``, it is
        treated as a full URI. Otherwise, it looks up the model name in
        the well-known names dictionary. But after this, in any case,
        we construct a URI in the form ``gpt://<folder_id>/<model>/<version>``.

        :param model_name: the name or URI of the model to call.
        :param model_version: the version of the model to use.
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


class Completions(BaseCompletions[GPTModel]):
    _model_type = GPTModel


class AsyncCompletions(BaseCompletions[AsyncGPTModel]):
    __doc__ = BaseCompletions.__doc__

    _model_type = AsyncGPTModel
