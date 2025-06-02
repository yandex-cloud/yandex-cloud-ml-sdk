from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from typing_extensions import Self


@dataclass(frozen=True)
class BaseModelConfig:
    def _validate_configure(self) -> None:
        pass

    def _validate_run(self) -> None:
        pass

    def _replace(self, **kwargs: dict) -> Self:
        return replace(self, **kwargs)

    def _asdict(self):
        return asdict(self)
