from __future__ import annotations

import os
import pathlib
from typing import Any, TypeVar, Union, cast, overload

from typing_extensions import TypeAlias, TypeGuard

_T = TypeVar('_T')
_D = TypeVar('_D')


class Undefined:
    """Class for making possible to differ None and not-passed default value.

    Sentinel until PEP 0661.
    """

    def __repr__(self):
        return 'Undefined'

#: Default, non-passed value
UNDEFINED = Undefined()
UndefinedOr = Union[_T, Undefined]


def is_defined(obj: _T | Undefined) -> TypeGuard[_T]:
    return obj is not UNDEFINED


# Overloads for better type inference
@overload
def get_defined_value(obj: UndefinedOr[_T], default: None) -> _T | None:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: str) -> _T | str:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: int) -> _T | int:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: float) -> _T | float:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: bool) -> _T | bool:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: list[Any]) -> _T | list[Any]:
    ...


# Специальный overload для пустого списка
@overload
def get_defined_value(obj: UndefinedOr[_T], default: list) -> _T | list:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: dict[Any, Any]) -> _T | dict[Any, Any]:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: PathLike) -> _T | PathLike:
    ...


@overload
def get_defined_value(obj: UndefinedOr[_T], default: _D) -> _T | _D:
    ...


def get_defined_value(obj: UndefinedOr[_T], default: _D) -> _T | _D:
    if is_defined(obj):
        return cast(_T, obj)

    return cast(_D, default)

#: Extension of os.PathLike with a string
PathLike: TypeAlias = Union[str, os.PathLike]


def is_path_like(path: Any) -> TypeGuard[PathLike]:
    return isinstance(path, (str, os.PathLike))


def coerce_path(path: PathLike) -> pathlib.Path:
    return pathlib.Path(path)
