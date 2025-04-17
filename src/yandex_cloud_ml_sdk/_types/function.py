from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic

from .model import ModelTypeT

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK
    from yandex_cloud_ml_sdk._types.domain import BaseDomain


class BaseFunction(abc.ABC):
    def __init__(self, name: str, sdk: BaseSDK, parent_resource: BaseDomain):
        self._name = name
        self._sdk = sdk
        self._parent_resource = parent_resource


class BaseModelFunction(BaseFunction, Generic[ModelTypeT]):
    _model_type: type[ModelTypeT]

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> ModelTypeT:
        pass
