from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, TypedDict


@dataclass(frozen=True)
class TextClassificationLabel(Mapping):
    """This class represents a label for text classification
    with an associated confidence score.
    """
    #: the label for the classification
    label: str
    #: the confidence score associated with the label
    confidence: float

    def __getitem__(self, key):
        return asdict(self)[key]

    def __iter__(self):
        return iter(asdict(self))

    def __len__(self):
        return len(asdict(self))


class TextClassificationSample(TypedDict):
    """This class represents a sample of text for classification."""
    #: the text to be classified
    text: str
    #: the expected label for the classification
    label: str
