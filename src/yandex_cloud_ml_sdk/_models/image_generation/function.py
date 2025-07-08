from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .model import AsyncImageGenerationModel, ImageGenerationModel


class BaseImageGeneration(BaseModelFunction[ModelTypeT]):
    """
    A class for image generation models.

    It provides the functionality to call an image generation model by constructing
    the appropriate URI based on the provided model name and version.

    Returns a model's object through which requests to the backend are made.

    >>> model = sdk.models.image_generation('yandex-art')  # this is how the model is created
    """
    @override
    def __call__(
        self,
        model_name: str,
        *,
        model_version: str = 'latest',
    ):
        """
        Call the image generation model with the specified name and version.

        Constructs the URI for the model based on the provided model's name
        and version. If the name contains ``://``, it is treated as a
        complete URI. Otherwise, it looks up the model name in
        the well-known names dictionary. But after this, in any case,
        we construct a URI in the form ``art://<folder_id>/<model>/<version>``.

        :param model_name: the name or URI of the model to call.
        :param model_version: the version of the model to use.
            Defaults to 'latest'.
        """
        if '://' in model_name:
            uri = model_name
        else:
            folder_id = self._sdk._folder_id
            uri = f'art://{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )

@doc_from(BaseImageGeneration)
class ImageGeneration(BaseImageGeneration):
    _model_type = ImageGenerationModel

@doc_from(BaseImageGeneration)
class AsyncImageGeneration(BaseImageGeneration):
    _model_type = AsyncImageGenerationModel
