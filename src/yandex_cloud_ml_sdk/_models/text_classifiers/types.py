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
        """Retrieve the value associated with the given key.
        If the key is not found in the label or confidence attributes will raise the error.
        """
        return asdict(self)[key]

    def __iter__(self):
        """Return an iterator over the items (key-value pairs) of the label."""
        return iter(asdict(self))

    def __len__(self):
        """Return the number of items in the label."""
        return len(asdict(self))


class TextClassificationSample(TypedDict):
    """This class represents a sample of text for classification."""
    #: the text to be classified
    text: str
    #: the expected label for the classification
    label: str
