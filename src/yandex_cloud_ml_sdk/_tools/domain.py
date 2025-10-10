# pylint: disable=protected-access
from __future__ import annotations

from functools import cached_property
from typing import Generic

from yandex_cloud_ml_sdk._search_api.generative.config import SmartFilterSequence
from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.string import SmartStringSequence
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids

from .function import AsyncFunctionTools, FunctionTools, FunctionToolsTypeT
from .generative_search import GenerativeSearchTool
from .search_index.call_strategy import CallStrategy, CallStrategyInputType
from .search_index.rephraser.function import RephraserFunction, RephraserInputType
from .search_index.tool import SearchIndexTool


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
        call_strategy: UndefinedOr[CallStrategyInputType] = UNDEFINED,
    ) -> SearchIndexTool:
        """Creates SearchIndexTool (not to be confused with :py:class:`~.SearchIndex`/:py:class:`~.AsyncSearchIndex`).

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

        call_strategy_ = None
        if is_defined(call_strategy):
            call_strategy_ = CallStrategy._coerce(call_strategy)

        return SearchIndexTool(
            search_index_ids=tuple(index_ids),
            max_num_results=max_num_results_,
            rephraser=rephraser_,
            call_strategy=call_strategy_,
        )

    def generative_search(
        self,
        *,
        description: str,
        site: UndefinedOr[SmartStringSequence] = UNDEFINED,
        host: UndefinedOr[SmartStringSequence] = UNDEFINED,
        url: UndefinedOr[SmartStringSequence] = UNDEFINED,
        enable_nrfm_docs: UndefinedOr[bool] = UNDEFINED,
        search_filters: UndefinedOr[SmartFilterSequence] = UNDEFINED,
    ) -> GenerativeSearchTool:
        """Creates GeberativeSearch tool which provide access to
        generative search by `Search API <https://yandex.cloud/docs/search-api>`_ for LLMs.

        Not to be confused with ``sdk.search_api.generative``.
        Tools domain is for creating tools for using in LLMs/Assistants and search_api domain
        is for using Search API directly.

        To learn more about parameters and their formats and possible values,
        refer to
        `generative search documentation <https://yandex.cloud/docs/search-api/concepts/generative-response#body>`_

        NB: All of the ``site``, ``host``, ``url`` parameters are mutually exclusive.

        :param site: parameter for limiting search to specific location or list of sites.
        :param host: parameter for limiting search to specific location or list of hosts.
        :param url: parameter for limiting search to specific location or list of URLs.
        :param enable_nrfm_docs: tells to backend to include or not to include pages,
            which are not available via direct clicks from given sites/hosts/urls
            to search result.
        :param search_filters: allows to limit search results with additional filters.

            >>> date_filter = {'date': '<20250101'}
            >>> format_filter = {'format': 'doc'}
            >>> lang_filter = {'lang': 'ru'}
            >>> tool = sdk.tools.generative_search(
            ...     search_filters=[date_filter, format_filter, lang_filter],
            ...     description="description when model should call a tool"
            ... )

        """

        search_api = self._sdk.search_api.generative(
            site=site,
            host=host,
            url=url,
            enable_nrfm_docs=enable_nrfm_docs,
            search_filters=search_filters
        )
        return search_api.as_tool(description=description)


class AsyncTools(BaseTools[AsyncFunctionTools]):
    _functions_impl = AsyncFunctionTools


class Tools(BaseTools[FunctionTools]):
    _functions_impl = FunctionTools
