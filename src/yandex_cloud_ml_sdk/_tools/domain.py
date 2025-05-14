# pylint: disable=protected-access
from __future__ import annotations

from functools import cached_property
from typing import Generic

from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids

from .function import AsyncFunctionTools, FunctionTools, FunctionToolsTypeT
from .rephraser.function import RephraserFunction, RephraserInputType
from .tool import SearchIndexTool


class BaseTools(BaseDomain, Generic[FunctionToolsTypeT]):
    _functions_impl: type[FunctionToolsTypeT]

    @cached_property
    def function(self) -> FunctionToolsTypeT:
        return self._functions_impl(
            name='tools.function',
            sdk=self._sdk
        )

    @cached_property
    def rephraser(self) -> RephraserFunction:
        return RephraserFunction(
            name='tools.rehraser',
            sdk=self._sdk,
            parent_resource=self
        )

    def search_index(
        self,
        indexes: ResourceType[BaseSearchIndex],
        *,
        max_num_results: UndefinedOr[int] = UNDEFINED,
        rephraser: UndefinedOr[RephraserInputType] = UNDEFINED,
    ) -> SearchIndexTool:
        """Creates SearchIndexTool (not to be confused with :py:class:`~.SearchIndex`).

        :param indexes: parameter takes :py:class:`~.BaseSearchIndex`, string with search index id,
            or a list of this values in any combination.
        :param max_num_results: the maximum number of results to return from the search.
            Fewer results may be returned if necessary to fit within the prompt's token limit.
            This ensures that the combined prompt and search results do not exceed the token constraints.
        :param rephraser: setting for rephrasing user queries; refer to :py:class:`~.Rephraser` documentation
            for details.
        """

        index_ids = coerce_resource_ids(indexes, BaseSearchIndex)
        max_num_results_ = get_defined_value(max_num_results, None)

        rephraser_ = None
        if is_defined(rephraser):
            # this is coercing any RephraserInputType to Rephraser
            rephraser_ = self.rephraser(rephraser)  # type: ignore[arg-type]

        return SearchIndexTool(
            search_index_ids=tuple(index_ids),
            max_num_results=max_num_results_,
            rephraser=rephraser_,
        )


class AsyncTools(BaseTools[AsyncFunctionTools]):
    _functions_impl = AsyncFunctionTools


class Tools(BaseTools[FunctionTools]):
    _functions_impl = FunctionTools
