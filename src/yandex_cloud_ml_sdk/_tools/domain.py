# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids

from .tool import SearchIndexTool


class Tools(BaseDomain):
    def search_index(
        self,
        indexes: ResourceType[BaseSearchIndex],
        *,
        max_num_results: UndefinedOr[int] = UNDEFINED,
    ):
        index_ids = coerce_resource_ids(indexes, BaseSearchIndex)
        max_num_results_ = get_defined_value(max_num_results, None)
        return SearchIndexTool(
            search_index_ids=tuple(index_ids),
            max_num_results=max_num_results_
        )
