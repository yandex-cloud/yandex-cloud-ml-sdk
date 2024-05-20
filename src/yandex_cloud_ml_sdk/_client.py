from __future__ import annotations

from typing import Any

from grpc import aio, ssl_channel_credentials
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub
from yandexcloud._sdk import _service_for_ctor


class AsyncCloudClient:
    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        service_map: dict[str, str],
    ):
        self._endpoint = endpoint
        self._api_key = api_key

        self._service_map_override: dict[str, str] = service_map
        self._service_map: dict[str, str] = {}

    async def _init_service_map(self):
        credentials = ssl_channel_credentials()
        async with aio.secure_channel(self._endpoint, credentials) as channel:
            stub = ApiEndpointServiceStub(channel)
            response = await stub.List(ListApiEndpointsRequest())
            for endpoint in response.endpoints:
                self._service_map[endpoint.id] = endpoint.address

        # TODO: add a validation for unknown services in override
        self._service_map.update(self._service_map_override)

    async def get_service_client(self, stub: Any) -> aio.Channel:
        service_name: str = _service_for_ctor(stub)

        if not self._service_map:
            await self._init_service_map()

        if not (endpoint := self._service_map.get(service_name)):
            raise ValueError(f'failed to find endpoint for {service_name=} and {stub=}')

        credentials = ssl_channel_credentials()
        return aio.secure_channel(endpoint, credentials)
