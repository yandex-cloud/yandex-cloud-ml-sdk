from __future__ import annotations

import asyncio

import pytest
# pylint: disable-next=no-name-in-module
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest, ListApiEndpointsResponse
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub

from yandex_cloud_ml_sdk import AsyncYCloudML


@pytest.mark.heavy
@pytest.mark.asyncio
async def test_multiple_requests(folder_id):
    async_sdk = AsyncYCloudML(folder_id=folder_id)
    test_client = async_sdk._client

    stubs = []
    ctx = []
    for _ in range(20000):
        context = test_client.get_service_stub(ApiEndpointServiceStub, 10)
        ctx.append(context)
        stub = await context.__aenter__()  # pylint: disable=no-member
        stubs.append(stub)

    coros = []
    for stub in stubs:
        coro = test_client.call_service(
            stub.List,
            ListApiEndpointsRequest(),
            timeout=60,
            expected_type=ListApiEndpointsResponse,
            auth=False
        )
        coros.append(coro)

    await asyncio.gather(*coros)

    for context in ctx:
        await context.__aexit__(None, None, None)
