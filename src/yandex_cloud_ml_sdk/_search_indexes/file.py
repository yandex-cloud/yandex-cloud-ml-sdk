from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from yandex_cloud_ml_sdk._types.resource import BaseResource


@dataclass(frozen=True)
class SearchIndexFile(BaseResource):
    search_index_id: str
    created_by: str
    created_at: datetime
