from __future__ import annotations

from collections.abc import Mapping

from typing_extensions import override

from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownInput, UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .config import FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder, WebSearchConfig
from .web import AsyncWebSearch, WebSearch, WebSearchTypeT


class BaseWebSearchFunction(BaseModelFunction[WebSearchTypeT]):
    """Web search function for creating search object which provides
    methods for invoking web search.
    """

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
        search_type: EnumWithUnknownInput[SearchType],
        *,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] = UNDEFINED,
        fix_typo_mode: UndefinedOrEnumWithUnknownInput[FixTypoMode] = UNDEFINED,
        localization: UndefinedOrEnumWithUnknownInput[Localization] = UNDEFINED,
        sort_order: UndefinedOrEnumWithUnknownInput[SortOrder] = UNDEFINED,
        sort_mode: UndefinedOrEnumWithUnknownInput[SortMode] = UNDEFINED,
        group_mode: UndefinedOrEnumWithUnknownInput[GroupMode] = UNDEFINED,
        groups_on_page: UndefinedOr[int] = UNDEFINED,
        docs_in_group: UndefinedOr[int] = UNDEFINED,
        max_passages: UndefinedOr[int] = UNDEFINED,
        region: UndefinedOr[str] = UNDEFINED,
        user_agent: UndefinedOr[str] = UNDEFINED,
        metadata: UndefinedOr[Mapping[str, str]] = UNDEFINED,
    ) -> WebSearchTypeT:
        """
        Creates web search object which provides methods for web search.

        To learn more about parameters and their formats and possible values,
        refer to
        `web search documentation <https://yandex.cloud/ru/docs/search-api/concepts/web-search#parameters>`_

        :param search_type: Search type.
        :param family_mode: Results filtering.
        :param fix_typo_mode: Search query typo correction setting
        :param localization: Search response notifications language.
            Affects the text in the ``found-docs-human`` tag and error messages
        :param sort_order: Search results sorting order
        :param sort_mode: Search results sorting mode rule
        :param group_mode: Result grouping method.
        :param groups_on_page: Maximum number of groups that can be returned per page.
        :param docs_in_group: Maximum number of documents that can be returned per group.
        :param max_passages: Maximum number of passages that can be used when generating
            a document.
        :param region: Search country or region ID that affects the document ranking rules.
        :param user_agent: String containing the User-Agent header.
            Use this parameter to have your search results optimized for a
            specific device and browser, including mobile search results.
        """
        config = WebSearchConfig(
            search_type=SearchType._coerce(search_type)
        )
        search_api = self._model_type(sdk=self._sdk, uri='<search_api>', config=config)

        return search_api.configure(
            family_mode=family_mode,
            fix_typo_mode=fix_typo_mode,
            localization=localization,
            sort_order=sort_order,
            sort_mode=sort_mode,
            group_mode=group_mode,
            groups_on_page=groups_on_page,
            docs_in_group=docs_in_group,
            max_passages=max_passages,
            region=region,
            user_agent=user_agent,
            metadata=metadata,
        )


@doc_from(BaseWebSearchFunction)
class WebSearchFunction(BaseWebSearchFunction[WebSearch]):
    _model_type = WebSearch


@doc_from(BaseWebSearchFunction)
class AsyncWebSearchFunction(BaseWebSearchFunction[AsyncWebSearch]):
    _model_type = AsyncWebSearch
