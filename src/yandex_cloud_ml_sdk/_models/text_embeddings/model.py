# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing_extensions import override
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
            return TextEmbeddingsModelResult._from_proto(response)


class AsyncTextEmbeddingsModel(BaseTextEmbeddingsModel):
    run = BaseTextEmbeddingsModel._run


class TextEmbeddingsModel(BaseTextEmbeddingsModel):
    run = run_sync(BaseTextEmbeddingsModel._run)
