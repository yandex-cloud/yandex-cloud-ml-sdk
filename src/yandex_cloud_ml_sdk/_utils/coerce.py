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
    """Coerce resource objects or IDs into a tuple of string IDs.
    
    Converts various resource representations (single resource, string ID,
    or iterable of resources/IDs) into a standardized tuple of string IDs.
    
    :param resources: Resource(s) to coerce. Can be a string ID, resource object,
                     or iterable of string IDs/resource objects.
    :param resource_type: The expected resource type for validation.
    """
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
    """Coerce a single value or iterable into a tuple of specified type.
    
    Converts a single value of the expected type or an iterable of values
    into a standardized tuple format.
    
    :param value: Value(s) to coerce. Can be a single value of the expected type
                 or an iterable of values.
    :param value_type: The expected type for validation of single values.
    """
    if isinstance(value, value_type):
        return (value, )

    if not isinstance(value, Iterable):
        raise TypeError(f'{value} expected to be {value_type} or Iterable')

    return tuple(value)
