# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from yandex.cloud.ai.assistants.v1.searchindex.search_index_file_pb2 import SearchIndexFile as ProtoSearchIndexFile

from yandex_cloud_ml_sdk._types.resource import BaseResource

from .chunking_strategy import BaseIndexChunkingStrategy

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclass(frozen=True)
class SearchIndexFile(BaseResource):
    search_index_id: str
    created_by: str
    created_at: datetime
    chunking_strategy: BaseIndexChunkingStrategy

    @classmethod
    def _kwargs_from_message(
        cls,
        proto: ProtoSearchIndexFile,  # type: ignore[override]
        sdk: BaseSDK
    ) -> dict[str, Any]:
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        # pylint: disable=protected-access
        kwargs['chunking_strategy'] = BaseIndexChunkingStrategy._from_upper_proto(
            proto=proto.chunking_strategy, sdk=sdk
        )
        return kwargs
