from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from typing_extensions import Self

from yandex_ai_studio_sdk._models.text_embeddings.config import TextEmbeddingsModelConfig
from yandex_ai_studio_sdk._types.schemas import QueryType

EncodingFormatType = Literal['float']


@dataclass(frozen=True)
class ChatEmbeddingsModelConfig(TextEmbeddingsModelConfig):
    dimensions: int | None = None
    encoding_format: EncodingFormatType | None = None
    extra_query: QueryType | None = None

    def _replace(self, **kwargs: Any) -> Self:
        extra_query: QueryType | None
        if extra_query := kwargs.get('extra_query'):
            assert isinstance(extra_query, dict)
            kwargs['extra_query'] = deepcopy(extra_query)

        return super()._replace(**kwargs)
