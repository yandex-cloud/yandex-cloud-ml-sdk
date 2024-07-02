from __future__ import annotations

from collections.abc import AsyncIterator
from concurrent import futures

import grpc.aio
import pytest
import pytest_asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML, YCloudML
from yandex_cloud_ml_sdk._auth import NoAuth
from yandex_cloud_ml_sdk._client import AsyncCloudClient
from yandex_cloud_ml_sdk._testing.client import MockClient
from yandex_cloud_ml_sdk._testing.interceptor import (
    AsyncUnaryStreamClientInterceptor, AsyncUnaryUnaryClientInterceptor, CassetteManager
)
from yandex_cloud_ml_sdk._types.misc import UNDEFINED

pytest_plugins = [
    'pytest_asyncio',
    'pytest_recording',
    'yandex_cloud_ml_sdk._testing.plugin',
]


@pytest.fixture(name='auth')
def fixture_auth(request):
    cassette_manager = CassetteManager(request)
    if cassette_manager.allow_grpc and cassette_manager.mode == 'write':
        return UNDEFINED  # it will trigger choosing of auth provider at client
    return NoAuth()


@pytest.fixture(name='interceptors')
def fixture_interceptors(request):
    cassette_manager = CassetteManager(request)
    return [
        AsyncUnaryUnaryClientInterceptor(cassette_manager),
        AsyncUnaryStreamClientInterceptor(cassette_manager),
    ]


@pytest.fixture(name='folder_id')
def fixture_folder_id():
    return 'b1ghsjum2v37c2un8h64'


@pytest.fixture(name='servicers')
def fixture_servicers():
    return []


@pytest_asyncio.fixture(name='test_server')
async def fixture_test_server():
    thread_pool = futures.ThreadPoolExecutor(max_workers=10000)
    server = grpc.aio.server(
        migration_thread_pool=thread_pool,
        options=(
            ('grpc.max_concurrent_streams', -1),
        )
    )
    port = server.add_insecure_port('[::]:0')
    server.port = port

    yield server

    await server.stop(None)


@pytest_asyncio.fixture(name='test_client')
async def test_client(auth, servicers, test_server) -> AsyncIterator[AsyncCloudClient | None]:
    if not servicers:
        yield None
        return

    for servicer, add_servicer in servicers:
        add_servicer(servicer, test_server)

    await test_server.start()

    yield MockClient(port=test_server.port, auth=auth)


@pytest_asyncio.fixture
def sdk(folder_id, interceptors, auth):
    return YCloudML(folder_id=folder_id, interceptors=interceptors, auth=auth)


@pytest_asyncio.fixture
def async_sdk(folder_id, interceptors, auth):
    return AsyncYCloudML(folder_id=folder_id, interceptors=interceptors, auth=auth)
