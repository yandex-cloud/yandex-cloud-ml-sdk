from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from typing_extensions import Self


@dataclass(frozen=True)
class BaseModelConfig:
    """
    Class for ML model configurations.

    This is a frozen dataclass that serves as a base for all model configuration classes.
    It provides common validation and utility methods for model configuration handling.

    The class is frozen to ensure immutability of configuration objects after creation.
    """

    def _validate_configure(self) -> None:
        pass

    def _validate_run(self) -> None:
        pass

    def _replace(self, **kwargs: Any) -> Self:
        return replace(self, **kwargs)

    def _asdict(self):
        return asdict(self)
