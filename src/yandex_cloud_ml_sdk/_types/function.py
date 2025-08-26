from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic

from .model import ModelTypeT

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK
    from yandex_cloud_ml_sdk._types.domain import BaseDomain


class BaseFunction(abc.ABC):
    """
    Class for all function types in the Yandex Cloud ML SDK.
    
    This class provides the foundation for implementing various function types
    that operate within the context of a domain and SDK instance.
    
    :param name: The name of the function.
    :param sdk: The SDK instance used for API communication.
    :param parent_resource: The parent domain resource that owns this function.
    """
    
    def __init__(self, name: str, sdk: BaseSDK, parent_resource: BaseDomain):
        self._name = name
        self._sdk = sdk
        self._parent_resource = parent_resource


class BaseModelFunction(BaseFunction, Generic[ModelTypeT]):
    """
    Class for functions that return model instances.
    
    This class extends BaseFunction to provide functionality for functions
    that work with specific model types. It uses generics to ensure type
    safety for the model instances returned by the function.
    
    :param ModelTypeT: The type of model that this function works with.
    """
    
    _model_type: type[ModelTypeT]

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> ModelTypeT:
        pass
