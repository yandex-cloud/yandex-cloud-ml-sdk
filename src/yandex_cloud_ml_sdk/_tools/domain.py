# pylint: disable=protected-access
from __future__ import annotations

from functools import cached_property
from typing import Generic

from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids

from .function import AsyncFunctionTools, FunctionTools, FunctionToolsTypeT
from .tool import SearchIndexTool


class BaseTools(BaseDomain, Generic[FunctionToolsTypeT]):
    _functions_impl: type[FunctionToolsTypeT]

    @cached_property
    def function(self) -> FunctionToolsTypeT:
        return self._functions_impl(
            name='tools.function',
            sdk=self._sdk
        )

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


class AsyncTools(BaseTools[AsyncFunctionTools]):
    _functions_impl = AsyncFunctionTools


class Tools(BaseTools[FunctionTools]):
    _functions_impl = FunctionTools
