from __future__ import annotations

import os
import pathlib
from typing import Any, TypeVar, Union, cast

from typing_extensions import TypeAlias, TypeGuard

_T = TypeVar('_T')
_D = TypeVar('_D')


class Undefined:
    """
    Class for making possible to differ None and not-passed default value.

    Sentinel until PEP 0661.
    """

    def __repr__(self):
        return 'Undefined'

#: Default, non-passed value
UNDEFINED = Undefined()
UndefinedOr = Union[_T, Undefined]


def is_defined(obj: _T | Undefined) -> TypeGuard[_T]:
    """
    Check if object is defined (not UNDEFINED).
    
    :param obj: Object to check
    """
    return obj is not UNDEFINED


def get_defined_value(obj: UndefinedOr[_T], default: _D) -> _T | _D:
    """
    Get defined value or return default if undefined.
    
    :param obj: Object that may be undefined
    :param default: Default value to return if obj is undefined
    """
    if is_defined(obj):
        return cast(_T, obj)

    return cast(_D, default)

#: Extension of os.PathLike with a string
PathLike: TypeAlias = Union[str, os.PathLike]


def is_path_like(path: Any) -> TypeGuard[PathLike]:
    """
    Check if object is path-like.
    
    :param path: Object to check
    """
    return isinstance(path, (str, os.PathLike))


def coerce_path(path: PathLike) -> pathlib.Path:
    """
    Convert path-like object to pathlib.Path.
    
    :param path: Path-like object to convert
    """
    return pathlib.Path(path)
