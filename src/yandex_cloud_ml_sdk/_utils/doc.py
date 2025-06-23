from __future__ import annotations

from typing import Callable, Union

from typing_extensions import TypeAlias

DocSourceType: TypeAlias = Union[type, Callable]


def doc_from(source: DocSourceType, **kwargs) -> Callable[[DocSourceType], DocSourceType]:
    def decorator(destination: DocSourceType) -> DocSourceType:
        doc = source.__doc__

        assert doc, 'source docstring cannot be empty'
        assert not destination.__doc__, 'destination docstring must be empty'

        if kwargs:
            doc = doc.format(**kwargs)

        destination.__doc__ = doc

        return destination

    return decorator
