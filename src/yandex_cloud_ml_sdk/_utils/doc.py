from __future__ import annotations

from typing import Callable, TypeVar, Union

from typing_extensions import ParamSpec, TypeAlias

P = ParamSpec('P')
T = TypeVar('T')
DocOutputType: TypeAlias = Callable[P, T]
DocSourceType: TypeAlias = Union[DocOutputType, property]


def doc_from(source: DocSourceType, **kwargs) -> Callable[[DocOutputType[P, T]], DocOutputType[P, T]]:
    def decorator(destination: DocOutputType[P, T]) -> DocOutputType[P, T]:
        doc = source.__doc__

        assert doc, 'source docstring cannot be empty'
        assert not destination.__doc__, 'destination docstring must be empty'

        if kwargs:
            doc = doc.format(**kwargs)

        destination.__doc__ = doc

        return destination

    return decorator
