from __future__ import annotations

from typing import Any


def model_match(model: Any, filters: dict[str, Any] | None) -> bool:
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
