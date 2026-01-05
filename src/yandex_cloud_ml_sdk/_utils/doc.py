from __future__ import annotations

from typing import Callable, TypeVar, Union

from typing_extensions import ParamSpec, TypeAlias

P = ParamSpec('P')
T = TypeVar('T')

DocSourceType: TypeAlias = Union[Callable, property, type]


def doc_from(source: DocSourceType, **kwargs: object) -> Callable[[T], T]:
    def decorator(destination: T) -> T:
        doc = source.__doc__

        assert doc, 'source docstring cannot be empty'
        assert not destination.__doc__, 'destination docstring must be empty'  # type: ignore[attr-defined]

        if kwargs:
            doc = doc.format(**kwargs)

        destination.__doc__ = doc  # type: ignore[attr-defined]

        return destination

    return decorator
