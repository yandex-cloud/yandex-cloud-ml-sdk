from __future__ import annotations

from typing import TYPE_CHECKING

from get_annotations import get_annotations

from .function import BaseModelFunction

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._client import AsyncCloudClient
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseDomain:
    """
    Domain class for Yandex Cloud ML SDK.
    
    This class provides the foundational structure for domain-specific functionality
    within the SDK, maintaining references to the SDK instance and providing access
    to the underlying client and folder configuration.
    
    :param name: The name of the domain.
    :param sdk: The base SDK instance.
    """
    # TODO: add some repr, description and such
    def __init__(self, name: str, sdk: BaseSDK):
        self._name = name
        self._sdk = sdk

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    @property
    def _folder_id(self) -> str:
        return self._sdk._folder_id


class DomainWithFunctions(BaseDomain):
    """
    Domain class that automatically initializes functions from type annotations.
    
    This class extends BaseDomain to provide automatic initialization of functions
    based on class type annotations. It scans for BaseModelFunction subclasses
    in the type annotations and creates instances of them as attributes.
    
    :param name: The name of the domain.
    :param sdk: The base SDK instance.
    """
    def __init__(self, name: str, sdk: BaseSDK):
        super().__init__(name=name, sdk=sdk)
        self._init_functions()

    def _init_functions(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member_class in members.items():
            if not issubclass(member_class, BaseModelFunction):
                continue
            function = member_class(name=member_name, sdk=self._sdk, parent_resource=self)
            setattr(self, member_name, function)
