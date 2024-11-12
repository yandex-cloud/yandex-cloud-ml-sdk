from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction, ModelTypeT

from .model import AsyncImageGenerationModel, ImageGenerationModel


class BaseImageGeneration(BaseModelFunction[ModelTypeT]):
    """@private"""

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
            uri = f'art://{folder_id}/{model_name}/{model_version}'

        return self._model_type(
            sdk=self._sdk,
            uri=uri,
        )


class ImageGeneration(BaseImageGeneration):
    """
    Synchronous API which returns
    `yandex_cloud_ml_sdk._models.image_generation.model.ImageGenerationModel`

    >>> import yandex_cloud_ml_sdk
    >>> sdk = yandex_cloud_ml_sdk.YCloudML(folder_id="...")
    >>> model: ImageGenerationModel = sdk.models.image_generation('yandex-art')
    >>> rc_model: ImageGenerationModel = sdk.models.image_generation('yandex-art', model_version="rc")
    """

    _model_type = ImageGenerationModel


class AsyncImageGeneration(BaseImageGeneration):
    """
    Asynchronous API which returns
    `yandex_cloud_ml_sdk._models.image_generation.model.AsyncImageGenerationModel`

    >>> import yandex_cloud_ml_sdk
    >>> sdk = yandex_cloud_ml_sdk.AsyncYCloudML(folder_id="...")
    >>> model: AsyncImageGenerationModel = sdk.models.image_generation('yandex-art')
    >>> rc_model: AsyncImageGenerationModel = sdk.models.image_generation('yandex-art', model_version="rc")
    """

    _model_type = AsyncImageGenerationModel
