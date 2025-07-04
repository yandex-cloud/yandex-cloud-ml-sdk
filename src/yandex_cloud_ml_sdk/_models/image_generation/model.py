# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing import cast

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_pb2 import (
    AspectRatio, ImageGenerationOptions
)
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_service_pb2 import (
    ImageGenerationRequest, ImageGenerationResponse
)
from yandex.cloud.ai.foundation_models.v1.image_generation.image_generation_service_pb2_grpc import (
    ImageGenerationAsyncServiceStub
)
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelAsyncMixin, OperationTypeT
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import ImageGenerationModelConfig
from .message import ImageMessageInputType, messages_to_proto
from .result import ImageGenerationModelResult


class BaseImageGenerationModel(
    ModelAsyncMixin[ImageGenerationModelConfig, ImageGenerationModelResult, OperationTypeT],
):
    """A class of the one, concrete model. This model encapsulates the URI and configuration."""
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
        Configures the image generation model with specified parameters and
        returns the configured instance of the model.

        :param seed: a random seed for generation.
        :param width_ratio: the width ratio for the generated image.
        :param height_ratio: the height ratio for the generated image.
        :param mime_type: the MIME type of the generated image.
            Read more on what MIME types exist in `the documentation <https://yandex.cloud/docs/foundation-models/image-generation/api-ref/ImageGenerationAsync/generate>`_.
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
                result_type=self._result_type,
                proto_result_type=ImageGenerationResponse
            )


@doc_from(BaseImageGenerationModel)
class AsyncImageGenerationModel(BaseImageGenerationModel[AsyncOperation[ImageGenerationModelResult]]):
    _operation_type = AsyncOperation[ImageGenerationModelResult]

    async def run_deferred(
        self,
        messages: ImageMessageInputType,
        *,
        timeout: float = 60,
    ) -> AsyncOperation[ImageGenerationModelResult]:
        """Executes the image generation operation asynchronously
        and returns an operation representing the ongoing image generation process.

        :param messages: the input messages for image generation.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._run_deferred(
            messages=messages,
            timeout=timeout
        )

    async def attach_deferred(
        self,
        operation_id: str,
        timeout: float = 60,
    ) -> AsyncOperation[ImageGenerationModelResult]:
        """Attaches to an ongoing image generation operation.

        :param operation_id: the ID of the operation to attach to.
        :param timeout: the timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        return await self._attach_deferred(operation_id=operation_id, timeout=timeout)


@doc_from(BaseImageGenerationModel)
class ImageGenerationModel(BaseImageGenerationModel[Operation[ImageGenerationModelResult]]):
    _operation_type = Operation[ImageGenerationModelResult]
    __run_deferred = run_sync(BaseImageGenerationModel[Operation[ImageGenerationModelResult]]._run_deferred)
    __attach_deferred = run_sync(BaseImageGenerationModel[Operation[ImageGenerationModelResult]]._attach_deferred)

    @doc_from(AsyncImageGenerationModel.run_deferred)
    def run_deferred(
        self,
        messages: ImageMessageInputType,
        *,
        timeout: float = 60,
    ) -> Operation[ImageGenerationModelResult]:
        # Mypy thinks that self.__run_deferred returns OperationTypeT instead of Operation
        return self.__run_deferred(  # type: ignore[return-value]
            messages=messages,
            timeout=timeout
        )

    @doc_from(AsyncImageGenerationModel.attach_deferred)
    def attach_deferred(self, operation_id: str, timeout: float = 60) -> Operation[ImageGenerationModelResult]:
        return cast(
            Operation[ImageGenerationModelResult],
            self.__attach_deferred(operation_id=operation_id, timeout=timeout)
        )
