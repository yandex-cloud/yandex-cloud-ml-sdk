# pylint: disable=protected-access
from __future__ import annotations

from functools import cached_property
from typing import Generic

from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .function import AsyncFunctionTools, FunctionTools, FunctionToolsTypeT
from .search_index.call_strategy import CallStrategy, CallStrategyInputType
from .search_index.rephraser.function import RephraserFunction, RephraserInputType
from .search_index.tool import SearchIndexTool


class BaseTools(BaseDomain, Generic[FunctionToolsTypeT]):
    """
    Class for tools functionality.

    Tools are specialized utilities that extend the capabilities of language models and AI assistants
    by providing access to external functions, data sources, and computational resources. They enable
    models to perform actions beyond text generation, such as searching through knowledge bases,
    executing custom functions, and processing structured data.

    This class serves as the foundation for tool management in both synchronous and asynchronous
    contexts, providing a unified interface for:

    - **Function Tools**: Custom Python functions that can be called by AI models during completions
    - **Search Index Tools**: Tools for querying and retrieving information from vector databases
      and search indexes
    - **Rephraser Tools**: Specialized models for query transformation and context enhancement

    Tools are particularly useful in:

    - **AI Assistants**: Extending conversational agents with external capabilities like web search,
      database queries, or API calls
    - **Completions**: Enabling language models to invoke functions during text generation for
      dynamic content creation and problem-solving

    The tools framework supports both streaming and non-streaming operations, making it suitable
    for real-time applications and batch processing scenarios.
    """
    _functions_impl: type[FunctionToolsTypeT]

    @cached_property
    def function(self) -> FunctionToolsTypeT:
        """
        Get the function sub-domain for creating function tools.
        """
        return self._functions_impl(
            name='tools.function',
            sdk=self._sdk
        )

    @cached_property
    def rephraser(self) -> RephraserFunction:
        """
        Get the rephraser for creating query transformation models.

        The rephraser provides access to specialized language models designed to intelligently
        rewrite and enhance user search queries by incorporating conversational context. This is
        particularly useful in multi-turn conversations where the latest user message may lack context
        from previous exchanges.

        The rephraser works by:
        - Analyzing the conversation history and current user query
        - Reformulating the query to be more specific and contextually complete
        - Improving search relevance by expanding abbreviated or ambiguous terms
        - Maintaining semantic intent while adding necessary context

        The rephraser returns a factory that can create Rephraser model instances with different
        configurations, supporting various model types including the default 'rephraser' model or
        custom rephrasing models.
        """
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
        """
        Creates SearchIndexTool (not to be confused with :py:class:`~.SearchIndex`/:py:class:`~.AsyncSearchIndex`).

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

@doc_from(BaseTools)
class AsyncTools(BaseTools[AsyncFunctionTools]):
    _functions_impl = AsyncFunctionTools

@doc_from(BaseTools)
class Tools(BaseTools[FunctionTools]):
    _functions_impl = FunctionTools
