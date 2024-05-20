from __future__ import annotations

from ._client import AsyncCloudClient
from ._types import UNDEFINED, UndefinedOr


class SDK:
    """Main entry point for SDK interactions."""

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
            api_key=api_key,
            service_map={} if service_map is UNDEFINED else service_map
        )
        self._folder_id = folder_id

    def _get_endpoint(self, endpoint: UndefinedOr[str]) -> str:
        # Here will be more logic, like parsing env vars and/or
        # ~/.config/yandex-cloud/config.yaml

        if endpoint is UNDEFINED:
            return 'api.cloud.yandex.net:443'

        return endpoint
