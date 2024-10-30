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

    return tuple(
        resource.id if isinstance(resource, resource_type) else resource
        for resource in resources
    )


def coerce_tuple(value: Iterable[_T] | _T, value_type: type[_T]) -> tuple[_T, ...]:
    if isinstance(value, value_type):
        return (value, )

    return tuple(value)
