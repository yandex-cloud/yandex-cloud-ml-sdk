from __future__ import annotations

from concurrent import futures
from typing import AsyncIterator, Callable
from unittest.mock import AsyncMock

import grpc.aio
import pytest
import pytest_asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML, YCloudML
from yandex_cloud_ml_sdk._auth import BaseAuth, NoAuth
from yandex_cloud_ml_sdk._client import AsyncCloudClient, _get_user_agent
from yandex_cloud_ml_sdk._retry import NoRetryPolicy, RetryPolicy
from yandex_cloud_ml_sdk._testing.client import MockClient
from yandex_cloud_ml_sdk._testing.interceptor import (
    AsyncUnaryStreamClientInterceptor, AsyncUnaryUnaryClientInterceptor, CassetteManager
)
from yandex_cloud_ml_sdk._types.misc import UNDEFINED


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


@pytest.fixture(autouse=True)
def patch_operation(request, monkeypatch):
    allow_grpc_test = bool(list(request.node.iter_markers('allow_grpc')))
    generate = request.config.getoption("--generate-grpc")
    regenerate = request.config.getoption("--regenerate-grpc")
    if not allow_grpc_test or generate or regenerate:
        return

    import yandex_cloud_ml_sdk._types.operation  # pylint: disable=import-outside-toplevel

    monkeypatch.setattr(
        yandex_cloud_ml_sdk._types.operation.OperationInterface,  # pylint: disable=protected-access
        '_sleep_impl',
        AsyncMock()
    )


@pytest.fixture(name='folder_id')
def fixture_folder_id():
    return 'b1ghsjum2v37c2un8h64'


@pytest.fixture(name='servicers')
def fixture_servicers():
    return []


@pytest_asyncio.fixture(name='test_server')
async def fixture_test_server():
    thread_pool = futures.ThreadPoolExecutor(max_workers=10000)
    # NB: server must be non-async, because it is breaks work of
    # our grpc client
    # https://github.com/grpc/grpc/issues/25364
    server = grpc.server(
        thread_pool=thread_pool,
        options=(
            ('grpc.max_concurrent_streams', -1),
        )
    )
    port = server.add_insecure_port('[::]:0')
    server.port = port

    yield server

    server.stop(None)


@pytest.fixture(name='retry_policy')
def fixture_retry_policy() -> RetryPolicy:
    return NoRetryPolicy()


@pytest_asyncio.fixture(name='test_client_maker')
async def fixture_test_client_maker(
    auth,
    servicers,
    test_server,
    retry_policy: RetryPolicy
) -> AsyncIterator[Callable[[], AsyncCloudClient] | None]:
    if not servicers:
        yield None
        return

    for servicer, add_servicer in servicers:
        add_servicer(servicer, test_server)

    test_server.start()

    def maker() -> AsyncCloudClient:
        return MockClient(port=test_server.port, auth=auth, retry_policy=retry_policy)

    yield maker


@pytest.fixture(name='test_client')
def fixture_test_client(test_client_maker) -> AsyncCloudClient | None:
    if test_client_maker:
        return test_client_maker()
    return None


@pytest_asyncio.fixture(name='sdk_maker')
def fixture_sdk_maker(
    folder_id,
    interceptors,
    auth: BaseAuth,
    retry_policy: RetryPolicy,
    test_client_maker,
) -> Callable[[], YCloudML]:
    def maker() -> YCloudML:
        sdk = YCloudML(folder_id=folder_id, interceptors=interceptors, auth=auth, retry_policy=retry_policy)
        if test_client_maker:
            sdk._client = test_client_maker()
        return sdk

    return maker


@pytest_asyncio.fixture(name='sdk')
def fixture_sdk(sdk_maker) -> YCloudML:
    return sdk_maker()


@pytest_asyncio.fixture(name='async_sdk')
def fixture_async_sdk(
    folder_id,
    interceptors,
    auth: BaseAuth,
    retry_policy: RetryPolicy,
    test_client: MockClient | None,
) -> AsyncYCloudML:
    sdk = AsyncYCloudML(
        folder_id=folder_id,
        interceptors=interceptors,
        auth=auth,
        retry_policy=retry_policy,
        service_map={
            # NOT SO TMP after all
            # to remove this, we need to regenerate all of assistant tests cassetes
            # and maybe change etalons in tests, so it needs some effort
            'ai-files': 'assistant.api.cloud.yandex.net',
            'ai-assistants': 'assistant.api.cloud.yandex.net',
        }
    )
    if test_client:
        sdk._client = test_client
    return sdk


@pytest.fixture(name='user_agent_tuple')
def fixture_user_agent_tuple():
    return ('grpc.primary_user_agent', _get_user_agent())
