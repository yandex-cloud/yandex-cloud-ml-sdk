from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union, cast

from typing_extensions import Self, override
from yandex_ai_studio_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder
)
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class WebSearchConfig(BaseModelConfig):
    #: Search type.
    search_type: EnumWithUnknownAlias[SearchType]
    #: Results filtering.
    family_mode: EnumWithUnknownAlias[FamilyMode] | None = None
    #: Search query typo correction setting
    fix_typo_mode: EnumWithUnknownAlias[FixTypoMode] | None = None
    #: Search response notifications language.
    #: Affects the text in the ``found-docs-human`` tag and error messages
    localization: EnumWithUnknownAlias[Localization] | None = None

    #: Search results sorting order
    sort_order: EnumWithUnknownAlias[SortOrder] | None = None
    #: Search results sorting mode rule
    sort_mode: EnumWithUnknownAlias[SortMode] | None = None

    #: Result grouping method.
    group_mode: EnumWithUnknownAlias[GroupMode] | None = None
    #: Maximum number of groups that can be returned per page.
    groups_on_page: int | None = None
    #: Maximum number of documents that can be returned per group.
    docs_in_group: int | None = None

    #: Maximum number of passages that can be used when generating a document
    max_passages: int | None = None
    #: Search country or region ID that affects the document ranking rules.
    region: str | None = None
    #: String containing the User-Agent header.
    user_agent: str | None = None

    metadata: dict[str, str] | None = None

    @override
    def _replace(self, **kwargs: Any) -> Self:
        enum: type[ProtoBasedEnum]
        for field, enum in (
            ('search_type', SearchType),
            ('family_mode', FamilyMode),
            ('fix_typo_mode', FixTypoMode),
            ('localization', Localization),
            ('sort_order', SortOrder),
            ('sort_mode', SortMode),
            ('group_mode', GroupMode),
        ):
            value = cast(Union[EnumWithUnknownInput, None], kwargs.get(field))
            if value is None:
                continue

            kwargs[field] = enum._coerce(value)

        metadata = kwargs.get('metadata')
        if metadata is not None:
            # copying and coercing from Mapping
            kwargs['metadata'] = dict(metadata)

        return super()._replace(**kwargs)
