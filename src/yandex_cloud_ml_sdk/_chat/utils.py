from __future__ import annotations

from typing import Any, TypedDict

class ModelFilter(TypedDict, total=False):
    """
    Options to filter models by owner, version, or fine-tuned status.

    Example:

    >>> filters = {'owner': 'alice', 'version': 'v2', 'fine_tuned': True}
    """

    owner: str
    version: str
    fine_tuned: bool

def model_match(model: Any, filters: ModelFilter | None) -> bool:
    """
    Checks whether the given model object matches all specified attribute filters.
    """

    filters = filters or {}
    for key, value in filters.items():
        if not hasattr(model, key):
            raise AttributeError(
                f"Filtering Error: model object does not have attribute '{key}'."
            )
        if getattr(model, key) != value:
            return False
    return True
