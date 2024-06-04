from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar

from .model import BaseModel

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


ModelTypeT = TypeVar('ModelTypeT', bound=BaseModel)


class BaseFunction(abc.ABC, Generic[ModelTypeT]):
    _model_type: type[ModelTypeT]

    def __init__(self, name: str, sdk: BaseSDK):
        self._name = name
        self._sdk = sdk

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> ModelTypeT:
        pass
