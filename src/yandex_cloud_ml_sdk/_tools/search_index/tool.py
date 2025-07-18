# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass

from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.common_pb2 import SearchIndexTool as ProtoSearchIndexTool

from yandex_cloud_ml_sdk._tools.tool import BaseTool, ProtoAssistantsTool, ProtoToolTypeT
from yandex_cloud_ml_sdk._types.proto import SDKType

from .call_strategy import CallStrategy
from .rephraser.model import Rephraser


@dataclass(frozen=True)
class SearchIndexTool(BaseTool[ProtoSearchIndexTool]):
    search_index_ids: tuple[str, ...]

    max_num_results: int | None = None
    rephraser: Rephraser | None = None
    call_strategy: CallStrategy | None = None

    @classmethod
    def _from_proto(cls, *, proto: ProtoSearchIndexTool, sdk: SDKType) -> SearchIndexTool:
        max_num_results: int | None = None
        if proto.HasField("max_num_results"):
            max_num_results = proto.max_num_results.value

        rephraser: Rephraser | None = None
        if proto.HasField("rephraser_options"):
            rephraser = Rephraser._from_proto(proto=proto.rephraser_options, sdk=sdk)

        call_strategy: CallStrategy | None = None
        if proto.HasField('call_strategy'):
            call_strategy = CallStrategy._from_proto(proto=proto.call_strategy, sdk=sdk)

        return cls(
            search_index_ids=tuple(proto.search_index_ids),
            max_num_results=max_num_results,
            rephraser=rephraser,
            call_strategy=call_strategy,
        )

    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        assert issubclass(proto_type, ProtoAssistantsTool)

        max_num_results: None | Int64Value = None
        if self.max_num_results is not None:
            max_num_results = Int64Value(value=self.max_num_results)

        rephraser = None
        if self.rephraser:
            rephraser = self.rephraser._to_proto()

        call_strategy = None
        if self.call_strategy:
            call_strategy = self.call_strategy._to_proto()

        return proto_type(
            search_index=ProtoSearchIndexTool(
                max_num_results=max_num_results,
                search_index_ids=self.search_index_ids,
                rephraser_options=rephraser,
                call_strategy=call_strategy,
            )
        )
