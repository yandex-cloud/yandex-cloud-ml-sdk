from __future__ import annotations

from typing import Callable, Union

from typing_extensions import TypeAlias

DocSourceType: TypeAlias = Union[type, Callable]
#: Type alias for objects that can serve as documentation sources.


def doc_from(source: DocSourceType, **kwargs) -> Callable[[DocSourceType], DocSourceType]:
    """
    Copy docstring from source object to destination object.

    This decorator function copies the docstring from a source object to a destination
    object. The docstring can be formatted using keyword arguments if provided.

    :param source: The source object from which to copy the docstring
    :param kwargs: Keyword arguments for string formatting of the docstring
    """
    def decorator(destination: DocSourceType) -> DocSourceType:
        doc = source.__doc__

        assert doc, 'source docstring cannot be empty'
        assert not destination.__doc__, 'destination docstring must be empty'

        if kwargs:
            doc = doc.format(**kwargs)

        destination.__doc__ = doc

        return destination

    return decorator
