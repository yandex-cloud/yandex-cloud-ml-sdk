# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import ChunkingStrategy as ProtoChunkingStrategy
from yandex.cloud.ai.assistants.v1.searchindex.common_pb2 import StaticChunkingStrategy as ProtoStaticChunkingStrategy

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseIndexChunkingStrategy(abc.ABC):
    """A class for an index chunking strategy, from which all other strategies are inherited."""
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto: Any, sdk: BaseSDK) -> BaseIndexChunkingStrategy:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoChunkingStrategy:
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoChunkingStrategy, sdk: BaseSDK) -> BaseIndexChunkingStrategy:
        if proto.HasField('static_strategy'):
            return StaticIndexChunkingStrategy._from_proto(
                proto=proto.static_strategy,
                sdk=sdk
            )
        raise NotImplementedError('chunking strategies other then static are not supported in this SDK version')


@dataclass(frozen=True)
class StaticIndexChunkingStrategy(BaseIndexChunkingStrategy):
    """
    This class implements a static chunking strategy (i.e. a specific strategy with specific properties).

    It is characterized by maximum chunk size and overlap in tokens.
    """
    #: the maximum size of each chunk in tokens
    max_chunk_size_tokens: int
    #: the number of overlapping tokens between consecutive chunks
    chunk_overlap_tokens: int

    @classmethod
    # pylint: disable=unused-argument
    def _from_proto(cls, proto: ProtoStaticChunkingStrategy, sdk: BaseSDK) -> StaticIndexChunkingStrategy:
        return cls(
            max_chunk_size_tokens=proto.max_chunk_size_tokens,
            chunk_overlap_tokens=proto.chunk_overlap_tokens
        )

    def _to_proto(self) -> ProtoChunkingStrategy:
        return ProtoChunkingStrategy(
            static_strategy=ProtoStaticChunkingStrategy(
                max_chunk_size_tokens=self.max_chunk_size_tokens,
                chunk_overlap_tokens=self.chunk_overlap_tokens
            )
        )
