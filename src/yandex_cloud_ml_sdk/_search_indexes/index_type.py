# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Union

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import HybridSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import TextSearchIndex, VectorSearchIndex

from .chunking_strategy import BaseIndexChunkingStrategy
from .combination_strategy import BaseIndexCombinationStrategy
from .normalization_strategy import IndexNormalizationStrategy

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


ProtoSearchIndexType = Union[TextSearchIndex, VectorSearchIndex, HybridSearchIndex]


@dataclass(frozen=True)
class BaseSearchIndexType(abc.ABC):
    _proto_field_name: ClassVar[str]
    chunking_strategy: BaseIndexChunkingStrategy | None = None

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto, sdk: BaseSDK) -> Self:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoSearchIndexType:
        pass

    @classmethod
    def _parse_chunking_strategy(cls, proto: ProtoSearchIndexType, sdk: BaseSDK) -> BaseIndexChunkingStrategy | None:
        if proto.HasField('chunking_strategy'):
            return BaseIndexChunkingStrategy._from_upper_proto(proto=proto.chunking_strategy, sdk=sdk)
        return None

    @classmethod
    def _from_upper_proto(cls, proto: ProtoSearchIndex, sdk: BaseSDK) -> BaseSearchIndexType:
        klasses = (
            TextSearchIndexType,
            VectorSearchIndexType,
            HybridSearchIndexType,
        )
        field_klasses = {klass._proto_field_name: klass for klass in klasses}
        # TODO: registering metaclass?
        for field, klass in field_klasses.items():
            if proto.HasField(field):  # type: ignore[arg-type]
                value = getattr(proto, field)
                return klass._from_proto(
                    proto=value,
                    sdk=sdk
                )
        raise NotImplementedError(
            f'search index types other than {list(field_klasses)} are not supported in this SDK version'
        )


@dataclass(frozen=True)
class TextSearchIndexType(BaseSearchIndexType):
    _proto_field_name: ClassVar[str] = 'text_search_index'

    @classmethod
    def _from_proto(cls, proto: TextSearchIndex, sdk: BaseSDK) -> TextSearchIndexType:
        return cls(
            chunking_strategy=cls._parse_chunking_strategy(proto, sdk),
        )

    def _to_proto(self) -> TextSearchIndex:
        chunking_strategy = self.chunking_strategy._to_proto() if self.chunking_strategy else None
        return TextSearchIndex(
            chunking_strategy=chunking_strategy
        )


@dataclass(frozen=True)
class VectorSearchIndexType(BaseSearchIndexType):
    _proto_field_name: ClassVar[str] = 'vector_search_index'

    doc_embedder_uri: str | None = None

    query_embedder_uri: str | None = None

    @classmethod
    def _from_proto(cls, proto: VectorSearchIndex, sdk: BaseSDK) -> VectorSearchIndexType:
        return cls(
            doc_embedder_uri=proto.doc_embedder_uri,
            query_embedder_uri=proto.query_embedder_uri,
            chunking_strategy=cls._parse_chunking_strategy(proto, sdk),
        )

    def _to_proto(self) -> VectorSearchIndex:
        chunking_strategy = self.chunking_strategy._to_proto() if self.chunking_strategy else None
        return VectorSearchIndex(
            chunking_strategy=chunking_strategy,
            doc_embedder_uri=self.doc_embedder_uri or '',
            query_embedder_uri=self.query_embedder_uri or '',
        )


@dataclass(frozen=True)
class HybridSearchIndexType(BaseSearchIndexType):
    _proto_field_name: ClassVar[str] = 'hybrid_search_index'

    text_search_index: TextSearchIndexType | None = None
    vector_search_index: VectorSearchIndexType | None = None
    normalization_strategy: IndexNormalizationStrategy | str | int | None = None
    combination_strategy: BaseIndexCombinationStrategy | None = None

    @classmethod
    def _from_proto(cls, proto: HybridSearchIndex, sdk: BaseSDK) -> HybridSearchIndexType:
        return cls(
            chunking_strategy=cls._parse_chunking_strategy(proto, sdk),
            text_search_index=TextSearchIndexType._from_proto(
                proto=proto.text_search_index,
                sdk=sdk,
            ),
            vector_search_index=VectorSearchIndexType._from_proto(
                proto=proto.vector_search_index,
                sdk=sdk,
            ),
            normalization_strategy=IndexNormalizationStrategy._coerce(proto.normalization_strategy),
            combination_strategy=BaseIndexCombinationStrategy._from_upper_proto(
                proto.combination_strategy, sdk=sdk
            )
        )

    def _to_proto(self) -> HybridSearchIndex:
        chunking_strategy = self.chunking_strategy._to_proto() if self.chunking_strategy else None
        text_search_index = self.text_search_index._to_proto() if self.text_search_index else None
        vector_search_index = self.vector_search_index._to_proto() if self.vector_search_index else None
        normalization_strategy = IndexNormalizationStrategy._coerce(
            self.normalization_strategy
        ) if self.normalization_strategy else 0
        combination_strategy = self.combination_strategy._to_proto() if self.combination_strategy else None

        return HybridSearchIndex(
            chunking_strategy=chunking_strategy,
            text_search_index=text_search_index,
            vector_search_index=vector_search_index,
            normalization_strategy=normalization_strategy,  # type: ignore[arg-type]
            combination_strategy=combination_strategy,
        )
