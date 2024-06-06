from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Sequence

from google.protobuf.message import Message
from grpc import aio, ssl_channel_credentials
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest  # pylint: disable=no-name-in-module
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub
from yandexcloud._sdk import _service_for_ctor


class AsyncCloudClient:
    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str | None,
        service_map: dict[str, str],
        interceptors: Sequence[aio.ClientInterceptor] | None,
    ):
        self._endpoint = endpoint
        self._api_key = api_key or os.getenv('YC_API_KEY')

        self._service_map_override: dict[str, str] = service_map
        self._service_map: dict[str, str] = {}
        self._interceptors = interceptors if interceptors else None

    async def _init_service_map(self, timeout: int):
        credentials = ssl_channel_credentials()
        async with aio.secure_channel(
            self._endpoint,
            credentials,
            interceptors=self._interceptors
        ) as channel:
            stub = ApiEndpointServiceStub(channel)
            response = await stub.List(ListApiEndpointsRequest(), timeout=timeout)  # type: ignore[misc]
            for endpoint in response.endpoints:
                self._service_map[endpoint.id] = endpoint.address

        # TODO: add a validation for unknown services in override
        self._service_map.update(self._service_map_override)

    @property
    def _metadata(self) -> tuple[tuple[str, str], ...]:
        if self._api_key:
            return (
                ('authorization', f'Api-Key {self._api_key}'),
            )
        return ()

    @asynccontextmanager
    async def get_service_stub(self, stub_class: Any, timeout: int) -> AsyncIterator[aio.Channel]:
        service_name: str = _service_for_ctor(stub_class)

        if not self._service_map:
            await self._init_service_map(timeout=timeout)

        if not (endpoint := self._service_map.get(service_name)):
            raise ValueError(f'failed to find endpoint for {service_name=} and {stub_class=}')

        credentials = ssl_channel_credentials()

        async with aio.secure_channel(
            endpoint,
            credentials,
            interceptors=self._interceptors
        ) as channel:
            yield stub_class(channel)

    async def call_service_stream(
        self,
        service: aio.UnaryStreamMultiCallable,
        request: Message,
        timeout: int,
    ) -> AsyncIterator[Message]:
        async for response in service(request, metadata=self._metadata, timeout=timeout):
            yield response

    async def call_service(
        self,
        service: aio.UnaryUnaryMultiCallable,
        request: Message,
        timeout: int,
    ) -> AsyncIterator[Message]:
        return await service(request, metadata=self._metadata, timeout=timeout)
