from __future__ import annotations

import abc

from typing_extensions import Self

from .proto import SDKType
from .schemas import JsonObject


class JsonBased(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _from_json(cls, *, data: JsonObject, sdk: SDKType) -> Self:
        raise NotImplementedError()
