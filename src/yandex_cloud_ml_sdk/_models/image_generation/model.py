# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_pb2 import (
    AspectRatio, ImageGenerationOptions
)
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_service_pb2 import ImageGenerationRequest
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_service_pb2_grpc import (
    ImageGenerationAsyncServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelAsyncMixin, OperationTypeT
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import ImageGenerationModelConfig
from .message import ImageMessageInputType, messages_to_proto
from .result import ImageGenerationModelResult


class BaseImageGenerationModel(
    ModelAsyncMixin[ImageGenerationModelConfig, ImageGenerationModelResult, OperationTypeT],
):
    """
    Base class for sync and async ImageGeneration models.
    """  # NB: we can't @private this because we need to pdoc configure method

    _config_type = ImageGenerationModelConfig
    _result_type = ImageGenerationModelResult
    _operation_type: type[OperationTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        seed: UndefinedOr[int] = UNDEFINED,
        width_ratio: UndefinedOr[int] = UNDEFINED,
        height_ratio: UndefinedOr[int] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
    ) -> Self:
        """
        Returns a copy of the model with config fields changed.

        :param seed: Seed of a run
        :param width_ratio: Width ratio
        :param height_ratio: Height_ratio
        :param mime_type: Mime type
        :type mime_type: str  # NB: pydoc ignores this
        """

        return super().configure(
            seed=seed,
            width_ratio=width_ratio,
            height_ratio=height_ratio,
            mime_type=mime_type,
        )

    @override
    # pylint: disable-next=arguments-differ
    async def _run_deferred(
        self,
        messages: ImageMessageInputType,
        *,
        timeout=60
    ) -> OperationTypeT:
        request = ImageGenerationRequest(
            model_uri=self._uri,
            messages=messages_to_proto(messages),
            generation_options=ImageGenerationOptions(
                mime_type=self.config.mime_type or '',
                seed=self.config.seed or 0,
                aspect_ratio=AspectRatio(
                    width_ratio=self.config.width_ratio or 0,
                    height_ratio=self.config.height_ratio or 0,
                )
            )
        )
        async with self._client.get_service_stub(ImageGenerationAsyncServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Generate,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )
            return self._operation_type(
                id=response.id,
                sdk=self._sdk,
                result_type=self._result_type
            )


class AsyncImageGenerationModel(BaseImageGenerationModel[AsyncOperation[ImageGenerationModelResult]]):
    """
    Async class for working with a image generation model
    """
    _operation_type = AsyncOperation[ImageGenerationModelResult]

    async def run_deferred(
        self,
        messages: ImageMessageInputType,
        *,
        timeout: float = 60,
    ) -> AsyncOperation[ImageGenerationModelResult]:
        """
        Run a model and return an `Operation`.

        >>> import yandex_cloud_ml_sdk
        >>> sdk = yandex_cloud_ml_sdk.AsyncYCloudML(folder_id='...')
        >>> model = sdk.models.image_generation('yandex-art')
        >>> operation = await model.run_deferred('kitten')
        >>> resullt: ImageGenerationModelResult = await operation
        """

        return await self._run_deferred(
            messages=messages,
            timeout=timeout
        )


class ImageGenerationModel(BaseImageGenerationModel[Operation[ImageGenerationModelResult]]):
    """
    Sync class for working with a image generation model
    """

    _operation_type = Operation[ImageGenerationModelResult]
    __run_deferred = run_sync(BaseImageGenerationModel[Operation[ImageGenerationModelResult]]._run_deferred)

    def run_deferred(
        self,
        messages: ImageMessageInputType,
        *,
        timeout: float = 60,
    ) -> Operation[ImageGenerationModelResult]:
        """
        Run a model and return an `Operation`.

        >>> import yandex_cloud_ml_sdk
        >>> sdk = yandex_cloud_ml_sdk.YCloudML(folder_id='...')
        >>> model = sdk.models.image_generation('yandex-art')
        >>> operation = model.run_deferred('kitten')
        >>> resullt: ImageGenerationModelResult = operation.wait()
        """

        # Mypy thinks that self.__run_deferred returns OperationTypeT instead of Operation
        return self.__run_deferred(  # type: ignore[return-value]
            messages=messages,
            timeout=timeout
        )
