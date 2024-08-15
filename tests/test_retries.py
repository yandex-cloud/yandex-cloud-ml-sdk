# pylint: disable=no-name-in-module,invalid-overridden-method
from __future__ import annotations

import time

import grpc
import pytest
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Token
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationServiceServicer, TokenizerServiceServicer, add_TextGenerationServiceServicer_to_server,
    add_TokenizerServiceServicer_to_server
)

from yandex_cloud_ml_sdk.retry import RetryPolicy


@pytest.fixture(name='retry_policy')
def fixture_retry_policy() -> RetryPolicy:
    return RetryPolicy(jitter=0, max_backoff=1.5)


@pytest.fixture
def servicers():
    class TextGenerationServicer(TextGenerationServiceServicer):
        def __init__(self):
            self.i = 0

        def Completion(self, request, context):
            self.i += 1
            time.sleep(0.1)
            if self.i == 1:
                context.abort(
                    grpc.StatusCode.UNAVAILABLE, "foo"
                )

            if self.i == 2:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED, "bar"
                )

            if self.i == 3:
                yield CompletionResponse(
                    alternatives=[],
                    usage=None,
                    model_version='111'
                )

            context.abort(
                grpc.StatusCode.CANCELLED, "special error"
            )

    class TokenizerService(TokenizerServiceServicer):
        def __init__(self):
            self.i = 0

        def TokenizeCompletion(self, request, context):
            self.i += 1
            time.sleep(0.1)

            if self.i == 1:
                context.abort(
                    grpc.StatusCode.UNAVAILABLE, "foo"
                )

            if self.i == 2:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED, "bar"
                )

            if self.i == 3:
                return TokenizeResponse(
                    tokens=[Token(id=1, text="abc", special=True)],
                    model_version="222"
                )

            context.abort(
                grpc.StatusCode.CANCELLED, "special error"
            )
            # to please pylint, because abort will raise a error
            return TokenizeResponse()

    return [
        (TextGenerationServicer(), add_TextGenerationServiceServicer_to_server),
        (TokenizerService(), add_TokenizerServiceServicer_to_server),
    ]


@pytest.mark.asyncio
async def test_retry_unary_unary(async_sdk):
    initial_time = time.time()
    result = await async_sdk.models.completions('foo').tokenize('bar')
    assert result[0].text == 'abc'
    assert result[0].id == 1
    assert result[0].special is True
    retry_delta = time.time() - initial_time
    assert retry_delta > 2.5

    initial_time = time.time()
    with pytest.raises(grpc.aio.AioRpcError, match='special error'):
        await async_sdk.models.completions('foo').tokenize('bar')
    retry_delta = time.time() - initial_time
    assert retry_delta < 1  # no retry


@pytest.mark.asyncio
async def test_retry_unary_stream(async_sdk):
    initial_time = time.time()
    result = await async_sdk.models.completions('foo').run('bar')
    assert result is not None
    assert not result.alternatives
    retry_delta = time.time() - initial_time
    assert retry_delta > 2.5

    initial_time = time.time()
    with pytest.raises(grpc.aio.AioRpcError, match='special error'):
        result = await async_sdk.models.completions('foo').run('bar')
    retry_delta = time.time() - initial_time
    assert retry_delta < 1  # no retry


@pytest.mark.asyncio
async def test_retry_deadline(async_sdk):
    initial_time = time.time()
    with pytest.raises(grpc.aio.AioRpcError, match='DEADLINE'):
        await async_sdk.models.completions('foo').run('bar', timeout=1)
    retry_delta = time.time() - initial_time
    assert 1 <= retry_delta < 2
