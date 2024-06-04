from __future__ import annotations

from get_annotations import get_annotations

from ._client import AsyncCloudClient
from ._models import AsyncModels, Models
from ._types.misc import UNDEFINED, Undefined, UndefinedOr
from ._types.resource import BaseResource


class BaseSDK:
    def __init__(
        self,
        *,
        folder_id: str,
        endpoint: UndefinedOr[str] = UNDEFINED,
        api_key: UndefinedOr[str] = UNDEFINED,
        service_map: UndefinedOr[dict[str, str]] = UNDEFINED,
    ):
        """
        Construct a new asynchronous sdk instance.

        :param folder_id: Yandex Cloud folder identifier which will be billed
           for models usage.
        :type folder_id: str
        :param endpoint: domain:port pair for Yandex Cloud API or any other
            grpc compatible target.
        :type endpoint: str
        :param api_key: highly WIP authorization way.
        :type api_key: str
        :param service_map: a way to redefine endpoints for one or more cloud subservices
            with a format of dict {service_name: service_address}.
        :type service_map: Dict[str, str]

        """

        self._client = AsyncCloudClient(
            endpoint=self._get_endpoint(endpoint),
            api_key=None if isinstance(api_key, Undefined) else api_key,
            service_map={} if isinstance(service_map, Undefined) else service_map
        )
        self._folder_id = folder_id

        self._init_resources()

    def _init_resources(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member_class in members.items():
            if issubclass(member_class, BaseResource):
                resource = member_class(name=member_name, sdk=self)
                setattr(self, member_name, resource)

    def _get_endpoint(self, endpoint: UndefinedOr[str]) -> str:
        # Here will be more logic, like parsing env vars and/or
        # ~/.config/yandex-cloud/config.yaml

        if isinstance(endpoint, Undefined):
            return 'api.cloud.yandex.net:443'

        return endpoint


class AsyncYCloudML(BaseSDK):
    models: AsyncModels


class YCloudML(BaseSDK):
    models: Models
