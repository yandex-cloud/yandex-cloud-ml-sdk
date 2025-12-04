from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union, cast

from typing_extensions import Self, override

from yandex_cloud_ml_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder
)
from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum
from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class TextToSpeechConfig(BaseModelConfig):

    @override
    def _replace(self, **kwargs: Any) -> Self:
        enum: type[ProtoBasedEnum]
        for field, enum in (
        ):
            value = cast(Union[EnumWithUnknownInput, None], kwargs.get(field))
            if value is None:
                continue

            kwargs[field] = enum._coerce(value)

        return super()._replace(**kwargs)
