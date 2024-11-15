from __future__ import annotations

from typing import Iterable, TypeVar, Union

from yandex_cloud_ml_sdk._types.resource import BaseResource

_T = TypeVar('_T')
ResourceTypeT = TypeVar('ResourceTypeT', bound=BaseResource)
ResourceType = Union[str, ResourceTypeT, Iterable[ResourceTypeT], Iterable[str]]


def coerce_resource_ids(
    resources: ResourceType[ResourceTypeT],
    resource_type: type[ResourceTypeT],
) -> tuple[str, ...]:
    if isinstance(resources, str):
        return (resources, )

    if isinstance(resources, resource_type):
        return (resources.id, )

    if not isinstance(resources, Iterable):
        raise TypeError(f'{resources} expected to be str, {resource_type} or Iterable')

    result: list[str] = []
    for resource in resources:
        if isinstance(resource, resource_type):
            result.append(resource.id)
        elif isinstance(resource, str):
            result.append(resource)
        else:
            raise TypeError(f'{resource} expected to be str or {resource_type}')

    return tuple(result)


def coerce_tuple(value: Iterable[_T] | _T, value_type: type[_T]) -> tuple[_T, ...]:
    if isinstance(value, value_type):
        return (value, )

    if not isinstance(value, Iterable):
        raise TypeError(f'{value} expected to be {value_type} or Iterable')

    return tuple(value)
