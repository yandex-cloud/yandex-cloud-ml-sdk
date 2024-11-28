# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing_extensions import Self, override
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2 import (
    TextEmbeddingRequest, TextEmbeddingResponse
)
from yandex.cloud.ai.foundation_models.v1.embedding.embedding_service_pb2_grpc import EmbeddingsServiceStub

from yandex_cloud_ml_sdk._types.model import ModelSyncMixin
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import TextEmbeddingsModelConfig
from .result import TextEmbeddingsModelResult


class BaseTextEmbeddingsModel(
    ModelSyncMixin[TextEmbeddingsModelConfig, TextEmbeddingsModelResult]
):
    _config_type = TextEmbeddingsModelConfig
    _result_type = TextEmbeddingsModelResult

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
    ) -> Self:
        return super().configure()

    def _make_request(
        self,
        *,
        text: str,
    ) -> TextEmbeddingRequest:
        return TextEmbeddingRequest(
            model_uri=self._uri,
            text=text,
        )

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        request = self._make_request(
            text=text,
        )
        async with self._client.get_service_stub(EmbeddingsServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.TextEmbedding,
                request,
                timeout=timeout,
                expected_type=TextEmbeddingResponse,
            )
            return TextEmbeddingsModelResult._from_proto(proto=response, sdk=self._sdk)


class AsyncTextEmbeddingsModel(BaseTextEmbeddingsModel):
    async def run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        return await self._run(
            text=text,
            timeout=timeout
        )


class TextEmbeddingsModel(BaseTextEmbeddingsModel):
    __run = run_sync(BaseTextEmbeddingsModel._run)

    def run(
        self,
        text: str,
        *,
        timeout=60,
    ) -> TextEmbeddingsModelResult:
        return self.__run(
            text=text,
            timeout=timeout
        )
