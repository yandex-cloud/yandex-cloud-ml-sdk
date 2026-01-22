from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Self, override

from yandex_ai_studio_sdk._search_api.enums import FamilyMode
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class ByImageSearchConfig(BaseModelConfig):
    family_mode: FamilyMode | None = None
    site: str | None = None

    @override
    def _replace(self, **kwargs: Any) -> Self:
        family_mode = kwargs.get('family_mode')
        if family_mode is not None:
            kwargs['family_mode'] = FamilyMode._coerce(family_mode)

        return super()._replace(**kwargs)
