from __future__ import annotations

from typing import TypeVar, Union

_T = TypeVar('_T')


class Undefined:
    """Sentinel until PEP 0661."""

    def __repr__(self):
        return 'Undefined'


UNDEFINED = Undefined()
UndefinedOr = Union[_T, Undefined]
