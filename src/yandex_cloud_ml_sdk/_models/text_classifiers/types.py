from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, TypedDict


@dataclass(frozen=True)
class TextClassificationLabel(Mapping):
    label: str
    confidence: float

    def __getitem__(self, key):
        return asdict(self)[key]

    def __iter__(self):
        return iter(asdict(self))

    def __len__(self):
        return len(asdict(self))


class TextClassificationSample(TypedDict):
    text: str
    label: str
