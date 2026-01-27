from __future__ import annotations

import abc
from xml.etree.ElementTree import Element

from typing_extensions import Self

from .proto import SDKType


class XMLBased(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _from_xml(cls, *, data: Element, sdk: SDKType) -> Self:
        raise NotImplementedError()
