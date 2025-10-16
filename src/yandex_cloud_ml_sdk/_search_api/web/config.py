from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union, cast

from typing_extensions import Self, override

from yandex_cloud_ml_sdk._search_api.types import (
    FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder
)
from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum
from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class WebSearchConfig(BaseModelConfig):
    search_type: EnumWithUnknownAlias[SearchType]
    family_mode: EnumWithUnknownAlias[FamilyMode] | None = None
    fix_typo_mode: EnumWithUnknownAlias[FixTypoMode] | None = None
    localization: EnumWithUnknownAlias[Localization] | None = None

    sort_order: EnumWithUnknownAlias[SortOrder] | None = None
    sort_mode: EnumWithUnknownAlias[SortMode] | None = None

    group_mode: EnumWithUnknownAlias[GroupMode] | None = None
    groups_on_page: int | None = None
    docs_in_group: int | None = None

    max_passages: int | None = None
    region: str | None = None
    user_agent: str | None = None

    metadata: dict[str, str] | None = None

    @override
    def _validate_configure(self) -> None:
        pass

    @override
    def _validate_run(self) -> None:
        pass

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
