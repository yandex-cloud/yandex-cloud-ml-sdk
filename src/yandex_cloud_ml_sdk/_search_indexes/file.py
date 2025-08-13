# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from yandex.cloud.ai.assistants.v1.searchindex.search_index_file_pb2 import SearchIndexFile as ProtoSearchIndexFile

from yandex_cloud_ml_sdk._types.resource import BaseResource


@dataclass(frozen=True)
class SearchIndexFile(BaseResource[ProtoSearchIndexFile]):
    search_index_id: str
    created_by: str
    created_at: datetime
