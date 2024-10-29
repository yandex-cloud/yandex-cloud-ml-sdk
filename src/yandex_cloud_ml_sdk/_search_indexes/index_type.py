# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import TextSearchIndex, VectorSearchIndex

from .chunking_strategy import BaseIndexChunkingStrategy

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


ProtoSearchIndexType = Union[TextSearchIndex, VectorSearchIndex]


@dataclass(frozen=True)
class BaseSearchIndexType(abc.ABC):
    chunking_strategy: BaseIndexChunkingStrategy | None = None

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto, sdk: BaseSDK) -> BaseSearchIndexType:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoSearchIndexType:
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoSearchIndex, sdk: BaseSDK) -> BaseSearchIndexType:
        if proto.HasField('text_search_index'):
            return TextSearchIndexType._from_proto(
                proto=proto.text_search_index,
                sdk=sdk
            )
        if proto.HasField('vector_search_index'):
            return VectorSearchIndexType._from_proto(
                proto=proto.vector_search_index,
                sdk=sdk
            )

        raise NotImplementedError('search index types other then text&vector are not supported in this SDK version')


@dataclass(frozen=True)
class TextSearchIndexType(BaseSearchIndexType):
    @classmethod
    def _from_proto(cls, proto: TextSearchIndex, sdk: BaseSDK) -> TextSearchIndexType:
        return cls(
            chunking_strategy=BaseIndexChunkingStrategy._from_upper_proto(
                proto=proto.chunking_strategy,
                sdk=sdk,
            )
        )

    def _to_proto(self) -> TextSearchIndex:
        chunking_strategy = self.chunking_strategy._to_proto() if self.chunking_strategy else None
        return TextSearchIndex(
            chunking_strategy=chunking_strategy
        )


@dataclass(frozen=True)
class VectorSearchIndexType(BaseSearchIndexType):
    doc_embedder_uri: str | None = None

    query_embedder_uri: str | None = None

    @classmethod
    def _from_proto(cls, proto: VectorSearchIndex, sdk: BaseSDK) -> VectorSearchIndexType:
        return cls(
            doc_embedder_uri=proto.doc_embedder_uri,
            query_embedder_uri=proto.query_embedder_uri,
            chunking_strategy=BaseIndexChunkingStrategy._from_upper_proto(
                proto=proto.chunking_strategy,
                sdk=sdk,
            )
        )

    def _to_proto(self) -> VectorSearchIndex:
        chunking_strategy = self.chunking_strategy._to_proto() if self.chunking_strategy else None
        return VectorSearchIndex(
            chunking_strategy=chunking_strategy,
            doc_embedder_uri=self.doc_embedder_uri or '',
            query_embedder_uri=self.query_embedder_uri or '',
        )
