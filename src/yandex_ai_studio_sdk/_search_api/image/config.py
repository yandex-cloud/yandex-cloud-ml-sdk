from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union, cast

from typing_extensions import Self, override
from yandex_ai_studio_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, ImageColor, ImageFormat, ImageOrientation, ImageSize, SearchType
)
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class ImageSearchConfig(BaseModelConfig):
    #: Search type.
    search_type: EnumWithUnknownAlias[SearchType]
    #: Results filtering.
    family_mode: EnumWithUnknownAlias[FamilyMode] | None = None
    #: Search query typo correction setting.
    fix_typo_mode: EnumWithUnknownAlias[FixTypoMode] | None = None
    #: Searching for images in a particular format.
    format: EnumWithUnknownAlias[ImageFormat] | None = None
    #: Searching for images of a particular size.
    size: EnumWithUnknownAlias[ImageSize] | None = None
    #: Searching for images with a particular orientation.
    orientation: EnumWithUnknownAlias[ImageOrientation] | None = None
    #: Searching for images containing a particular color.
    color: EnumWithUnknownAlias[ImageColor] | None = None
    #: Number of results per search result page.
    site: str | None = None
    #: Number of results per search result page.
    docs_on_page: int | None = None
    #: String containing the User-Agent header.
    user_agent: str | None = None

    @override
    def _replace(self, **kwargs: Any) -> Self:
        enum: type[ProtoBasedEnum]
        for field, enum in (
            ('search_type', SearchType),
            ('family_mode', FamilyMode),
            ('fix_typo_mode', FixTypoMode),
            ('format', ImageFormat),
            ('size', ImageSize),
            ('orientation', ImageOrientation),
            ('color', ImageColor),
        ):
            value = cast(Union[EnumWithUnknownInput, None], kwargs.get(field))
            if value is None:
                continue

            kwargs[field] = enum._coerce(value)

        return super()._replace(**kwargs)
