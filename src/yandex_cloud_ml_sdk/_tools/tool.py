# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.common_pb2 import SearchIndexTool as ProtoSearchIndexTool
from yandex.cloud.ai.assistants.v1.common_pb2 import Tool as ProtoTool

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseTool(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto: Any, sdk: BaseSDK) -> BaseTool:
        pass

    @abc.abstractmethod
    def _to_proto(self) -> ProtoTool:
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoTool, sdk: BaseSDK) -> BaseTool:
        if proto.HasField('search_index'):
            return SearchIndexTool._from_proto(
                proto=proto.search_index,
                sdk=sdk
            )
        raise NotImplementedError('tools other then search_index are not supported in this SDK version')


@dataclass(frozen=True)
class SearchIndexTool(BaseTool):
    search_index_ids: tuple[str, ...]

    max_num_results: int | None = None

    @classmethod
    def _from_proto(cls, proto: ProtoSearchIndexTool, sdk: BaseSDK) -> SearchIndexTool:
        max_num_results: int | None = None
        if proto.HasField("max_num_results"):
            max_num_results = proto.max_num_results.value

        return cls(
            search_index_ids=tuple(proto.search_index_ids),
            max_num_results=max_num_results,
        )

    def _to_proto(self) -> ProtoTool:
        max_num_results: None | Int64Value = None
        if self.max_num_results is not None:
            max_num_results = Int64Value(value=self.max_num_results)

        return ProtoTool(
            search_index=ProtoSearchIndexTool(
                max_num_results=max_num_results,
                search_index_ids=self.search_index_ids
            )
        )
