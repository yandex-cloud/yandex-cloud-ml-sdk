# pylint: disable=no-name-in-module
from __future__ import annotations

import asyncio
import time
from multiprocessing.pool import ThreadPool

import grpc
import grpc.aio
import pytest
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Token
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationServiceServicer, TokenizerServiceServicer, add_TextGenerationServiceServicer_to_server,
    add_TokenizerServiceServicer_to_server
)
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest, ListApiEndpointsResponse
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub

import yandex_cloud_ml_sdk._client
from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._client import AsyncCloudClient, _get_user_agent, httpx_client
from yandex_cloud_ml_sdk.auth import NoAuth
from yandex_cloud_ml_sdk.exceptions import AioRpcError


@pytest.fixture(name='servicers')
def fixture_servicers():
    class TextGenerationServicer(TextGenerationServiceServicer):
        def __init__(self):
            self.i = 0

        def Completion(self, request, context):
            for key, value in context.invocation_metadata():
                if key == 'user-agent':
                    assert _get_user_agent() in value
                    assert 'grpc-python-asyncio' in value

            for i in range(10):
                self.i = i
                yield CompletionResponse(
                    alternatives=[],
                    usage=None,
                    model_version=str(i)
                )

                time.sleep(1)

    class TokenizerService(TokenizerServiceServicer):
        def TokenizeCompletion(self, request, context):
            time.sleep(1)
            return TokenizeResponse(
                tokens=[Token(id=1, text="abc")],
                model_version='foo',
            )

    return [
        (TextGenerationServicer(), add_TextGenerationServiceServicer_to_server),
        (TokenizerService(), add_TokenizerServiceServicer_to_server),
    ]


@pytest.mark.require_env('internet')
@pytest.mark.asyncio
async def test_multiple_requests(folder_id):
    async_sdk = AsyncYCloudML(folder_id=folder_id)
    test_client = async_sdk._client

    stubs = []
    ctx = []
    for _ in range(20000):
        context = test_client.get_service_stub(ApiEndpointServiceStub, 10)
        ctx.append(context)
        stub = await context.__aenter__()  # pylint: disable=no-member,unnecessary-dunder-call
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


@pytest.mark.asyncio
async def test_stream_cancel_async(async_sdk, servicers):
    """This tests shows, that after close, call is actually cancelled
    and server handler is stopped its work correctly.
    """
    result = async_sdk.models.completions('foo').run_stream('foo')

    assert (await result.__anext__()).model_version == "0"  # pylint: disable=unnecessary-dunder-call
    assert (await result.__anext__()).model_version == "1"  # pylint: disable=unnecessary-dunder-call
    await asyncio.sleep(0.5)
    await result.aclose()
    await asyncio.sleep(2)

    assert servicers[0][0].i == 2


def test_stream_cancel_sync(sdk, servicers):
    """This tests shows, that after close, call is actually cancelled
    and server handler is stopped its work correctly.
    """

    result = sdk.models.completions('foo').run_stream('foo')

    assert next(result).model_version == "0"
    assert next(result).model_version == "1"
    time.sleep(0.5)
    result.close()
    time.sleep(2)

    assert servicers[0][0].i == 2


def test_multiple_threads(sdk_maker, caplog):
    """
    grpc.aio works strangely and stars to raise a lot of errors in loop.callbacks
    if called from more then one thread.
    But because therse errors raises in callbacks, it doesn't propagate to control plane
    and just logs into asyncio error logger.
    """

    caplog.set_level('ERROR', logger='asyncio')
    def main(i):
        sdk = sdk_maker()
        result = sdk.models.completions('foo').tokenize(str(i))
        return result

    thread_pool = ThreadPool(processes=10)
    thread_pool.map(main, range(10))

    assert not caplog.records


@pytest.mark.asyncio
async def test_httpx_client():
    async with httpx_client() as client:
        assert client.headers['User-Agent'] == _get_user_agent()


# pylint: disable=protected-access
@pytest.mark.asyncio
async def test_x_data_logging(interceptors, retry_policy):
    def check_result(metadata, extra=None):
        retry = ('yc-ml-sdk-retry', 'NONE')
        for key, value in metadata:
            if retry == (key, value):
                continue
            if key == 'x-client-request-id':
                continue
            if (key, value) == extra:
                continue

            assert not (key, value)

    client = AsyncCloudClient(
        endpoint="foo",
        auth=NoAuth(),
        service_map={},
        yc_profile=None,
        retry_policy=retry_policy,
        interceptors=interceptors,
        enable_server_data_logging=None,
        credentials=None,
    )

    check_result(await client._get_metadata(auth_required=False, timeout=0))

    client = AsyncCloudClient(
        endpoint="foo",
        auth=NoAuth(),
        service_map={},
        yc_profile=None,
        retry_policy=retry_policy,
        interceptors=interceptors,
        enable_server_data_logging=True,
        credentials=None,
    )

    check_result(
        await client._get_metadata(auth_required=False, timeout=0),
        ('x-data-logging-enabled', "true"),
    )

    client = AsyncCloudClient(
        endpoint="foo",
        auth=NoAuth(),
        service_map={},
        yc_profile=None,
        retry_policy=retry_policy,
        interceptors=interceptors,
        enable_server_data_logging=False,
        credentials=None,
    )

    check_result(
        await client._get_metadata(auth_required=False, timeout=0),
        ('x-data-logging-enabled', "false"),
    )


@pytest.mark.asyncio
async def test_channel_credentials(folder_id):
    sdk = AsyncYCloudML(folder_id=folder_id)
    assert sdk._client._credentials is None
    sdk._client._new_channel('foo')

    creds = grpc.ssl_channel_credentials()
    sdk = AsyncYCloudML(folder_id=folder_id, grpc_credentials=creds)
    assert sdk._client._credentials is creds
    sdk._client._new_channel('foo')

    # this test checks if passed grpc_credentials is really used in
    # channel creation
    sdk = AsyncYCloudML(folder_id=folder_id, grpc_credentials=1)
    with pytest.raises(AttributeError, match="'int' object has no attribute '_credentials'"):
        sdk._client._new_channel('foo')


@pytest.mark.asyncio
async def test_grpc_base_exception(async_sdk, monkeypatch, test_server):
    result = await async_sdk.models.completions('foo').tokenize("bar")
    assert result

    def raise_call_service(*args, **kwargs):
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.INTERNAL,
            initial_metadata=grpc.aio.Metadata(),
            trailing_metadata=grpc.aio.Metadata(),
            details="some details",
            debug_error_string="some debug"
        )

    monkeypatch.setattr(yandex_cloud_ml_sdk._client.AsyncCloudClient, 'call_service', raise_call_service)

    with pytest.raises(AioRpcError) as exc_info:
        await async_sdk.models.completions('foo').tokenize("bar")
    exc = exc_info.value
    exc_repr = str(exc)

    assert '"some details"' in exc_repr
    assert '"some debug"' in exc_repr
    assert f'\tendpoint = "localhost:{test_server.port}"\n' in exc_repr
    assert '\tstub_class = TokenizerServiceStub\n' in exc_repr
    assert '\tauth_provider' not in exc_repr
    assert '\tx-client-request-id' not in exc_repr


@pytest.mark.asyncio
async def test_grpc_unauth_exception(async_sdk, monkeypatch, auth):
    result = await async_sdk.models.completions('foo').tokenize("bar")
    assert result

    def raise_call_service_unauth(*args, **kwargs):
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.UNAUTHENTICATED,
            initial_metadata=grpc.aio.Metadata(),
            trailing_metadata=grpc.aio.Metadata(),
            details="some details",
            debug_error_string="some debug"
        )

    monkeypatch.setattr(yandex_cloud_ml_sdk._client.AsyncCloudClient, 'call_service', raise_call_service_unauth)

    with pytest.raises(AioRpcError) as exc_info:
        await async_sdk.models.completions('foo').tokenize("bar")
    exc = exc_info.value
    exc_repr = str(exc)

    assert f'\tauth_provider = {auth.__class__.__name__}\n' in exc_repr
    assert '\tx-client-request-id' not in exc_repr


@pytest.mark.asyncio
async def test_grpc_request_id_in_initial_metadata_exception(async_sdk, monkeypatch):
    def raise_call_service_initial(*args, **kwargs):
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.INTERNAL,
            initial_metadata=grpc.aio.Metadata(('x-client-request-id', 'INITIAL')),
            trailing_metadata=grpc.aio.Metadata(),
            details="some details",
            debug_error_string="some debug"
        )

    monkeypatch.setattr(yandex_cloud_ml_sdk._client.AsyncCloudClient, 'call_service', raise_call_service_initial)

    with pytest.raises(AioRpcError) as exc_info:
        await async_sdk.models.completions('foo').tokenize("bar")
    exc = exc_info.value
    exc_repr = str(exc)

    assert '\tauth_provider' not in exc_repr
    assert '\tx-client-request-id = "INITIAL"\n' in exc_repr


@pytest.mark.asyncio
async def test_grpc_request_id_in_trailing_metadata_exception(async_sdk, monkeypatch):
    def raise_call_service_trailing(*args, **kwargs):
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.INTERNAL,
            initial_metadata=grpc.aio.Metadata(),
            trailing_metadata=grpc.aio.Metadata(('x-client-request-id', 'TRAILING')),
            details="some details",
            debug_error_string="some debug"
        )

    monkeypatch.setattr(yandex_cloud_ml_sdk._client.AsyncCloudClient, 'call_service', raise_call_service_trailing)

    with pytest.raises(AioRpcError) as exc_info:
        await async_sdk.models.completions('foo').tokenize("bar")
    exc = exc_info.value
    exc_repr = str(exc)

    assert '\tauth_provider' not in exc_repr
    assert '\tx-client-request-id = "TRAILING"\n' in exc_repr


@pytest.mark.asyncio
async def test_grpc_request_id_wrong_metadata_exception(async_sdk, monkeypatch):
    def raise_call_service_wrong(*args, **kwargs):
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.INTERNAL,
            initial_metadata=grpc.aio.Metadata(),
            trailing_metadata=(),
            details="some details",
            debug_error_string="some debug"
        )

    monkeypatch.setattr(yandex_cloud_ml_sdk._client.AsyncCloudClient, 'call_service', raise_call_service_wrong)

    with pytest.raises(AioRpcError) as exc_info:
        await async_sdk.models.completions('foo').tokenize("bar")
    exc = exc_info.value
    exc_repr = str(exc)

    assert '\tauth_provider' not in exc_repr
    assert '\tx-client-request-id = "grpc metadata was replaced with non-Metadata object"\n' in exc_repr
