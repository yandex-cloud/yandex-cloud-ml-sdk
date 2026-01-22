# pylint: disable=protected-access,redefined-builtin
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Union

from typing_extensions import Self, override

from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.model import ModelSyncMixin
from yandex_ai_studio_sdk._types.schemas import QueryType
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import ChatEmbeddingsModelConfig, EncodingFormatType
from .result import ChatEmbeddingsModelResult

ChatEmbeddingsInputType = Union[str, Sequence[str]]


class BaseChatEmbeddingsModel(
    ModelSyncMixin[ChatEmbeddingsModelConfig, ChatEmbeddingsModelResult]
):
    _config_type = ChatEmbeddingsModelConfig
    _result_type: type[ChatEmbeddingsModelResult]
    _proto_result_type = None

    # pylint: disable=useless-parent-delegation,arguments-differ
    def configure(  # type: ignore[override]
        self,
        *,
        dimensions: UndefinedOr[int] = UNDEFINED,
        encoding_format: UndefinedOr[EncodingFormatType] = UNDEFINED,
        extra_query: UndefinedOr[QueryType] = UNDEFINED,
    ) -> Self:
        return super().configure(
            dimensions=dimensions,
            encoding_format=encoding_format,
            extra_query=extra_query,
        )

    def _build_request_json(self, input: ChatEmbeddingsInputType) -> dict[str, Any]:
        normalized_input: list[str]
        if isinstance(input, str):
            normalized_input = [input]
        else:
            normalized_input = list(input)

        result: dict[str, Any] = {
            'model': self._uri,
            'input': normalized_input,
        }
        c = self._config
        if c.dimensions is not None:
            result['dimensions'] = c.dimensions

        if c.encoding_format is not None:
            result['encoding_format'] = c.encoding_format

        if c.extra_query is not None:
            result.update(c.extra_query)

        return result

    @override
    # pylint: disable-next=arguments-differ
    async def _run(
        self,
        input: ChatEmbeddingsInputType,
        *,
        timeout=180,
    ) -> ChatEmbeddingsModelResult:
        async with self._client.httpx_for_service('http_completions', timeout) as client:
            response = await client.post(
                '/embeddings',
                json=self._build_request_json(input),
                timeout=timeout,
            )
            response.raise_for_status()

        return ChatEmbeddingsModelResult._from_json(data=response.json(), sdk=self._sdk)


class AsyncChatEmbeddingsModel(BaseChatEmbeddingsModel):
    _result_type = ChatEmbeddingsModelResult

    async def run(
        self,
        input: ChatEmbeddingsInputType,
        *,
        timeout=180,
    ) -> ChatEmbeddingsModelResult:
        return await self._run(
            input=input,
            timeout=timeout
        )

class ChatEmbeddingsModel(BaseChatEmbeddingsModel):
    _result_type = ChatEmbeddingsModelResult
    __run = run_sync(BaseChatEmbeddingsModel._run)

    def run(
        self,
        input: ChatEmbeddingsInputType,
        *,
        timeout=180,
    ) -> ChatEmbeddingsModelResult:
        return self.__run(
            input=input,
            timeout=timeout
        )
