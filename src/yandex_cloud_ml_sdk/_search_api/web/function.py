from __future__ import annotations

from collections.abc import Mapping

from typing_extensions import override

from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownInput, UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr

from .config import FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder, WebSearchConfig
from .web import AsyncWebSearch, WebSearch, WebSearchTypeT


class BaseWebSearchFunction(BaseModelFunction[WebSearchTypeT]):
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


class WebSearchFunction(BaseWebSearchFunction[WebSearch]):
    _model_type = WebSearch


class AsyncWebSearchFunction(BaseWebSearchFunction[AsyncWebSearch]):
    _model_type = AsyncWebSearch
