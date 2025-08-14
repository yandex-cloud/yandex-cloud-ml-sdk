from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from yandex_cloud_ml_sdk._types.resource import BaseResource


@dataclass(frozen=True)
class SearchIndexFile(BaseResource):
    """This class represents a file associated with a search index."""
    #: the unique identifier for the search index
    search_index_id: str
    #: the identifier of the user or system that created the file
    created_by: str
    #: the timestamp when the file was created
    created_at: datetime
