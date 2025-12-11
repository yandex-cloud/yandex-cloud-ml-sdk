from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, TypeVar

from typing_extensions import Self


@dataclass(frozen=True)
class BaseModelConfig:
    def _validate_configure(self) -> None:
        pass

    def _validate_run(self) -> None:
        pass

    def _replace(self, **kwargs: Any) -> Self:
        new_config = replace(self, **kwargs)
        new_config._validate_configure()
        return new_config

    def _asdict(self):
        return asdict(self)


ConfigTypeT = TypeVar('ConfigTypeT', bound=BaseModelConfig)
