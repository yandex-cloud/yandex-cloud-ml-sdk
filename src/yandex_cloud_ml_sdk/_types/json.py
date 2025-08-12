from __future__ import annotations

import abc
from typing import Any

from typing_extensions import Self

from .proto import SDKType


class JsonBased(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _from_json(cls, *, data: dict[str, Any], sdk: SDKType) -> Self:
        raise NotImplementedError()
