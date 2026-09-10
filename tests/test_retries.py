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

from yandex_ai_studio_sdk.retry import RetryPolicy


@pytest.fixture(name='retry_policy')
def fixture_retry_policy(request) -> RetryPolicy:
    return getattr(request, 'param', RetryPolicy(jitter=0, max_backoff=1.5))


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
                return None

            if self.i == 2:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED, "bar"
                )
                return None

            if self.i == 3:
                yield CompletionResponse(
                    alternatives=[],
                    usage=None,
                    model_version='111'
                )
                return None

            context.abort(
                grpc.StatusCode.CANCELLED, "special error"
            )
            return None

    class TokenizerService(TokenizerServiceServicer):
        def __init__(self):
            self.i = 0
            self.slow_i = 0

        def TokenizeCompletion(self, request, context):
            if request.messages[0].text == 'slow-first-attempt':
                self.slow_i += 1
                if self.slow_i == 1:
                    time.sleep(0.25)

                return TokenizeResponse(
                    tokens=[Token(id=2, text='retried', special=False)],
                    model_version='attempt-timeout'
                )

            self.i += 1
            time.sleep(0.1)

            if self.i == 1:
                context.abort(
                    grpc.StatusCode.UNAVAILABLE, "foo"
                )
                return None

            if self.i == 2:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED, "bar"
                )
                return None

            if self.i == 3:
                return TokenizeResponse(
                    tokens=[Token(id=1, text="abc", special=True)],
                    model_version="222"
                )

            context.abort(
                grpc.StatusCode.CANCELLED, "special error"
            )
            return None

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


@pytest.mark.parametrize(
    'retry_policy',
    [
        RetryPolicy(
            max_attempts=3,
            initial_backoff=0,
            max_backoff=0,
            jitter=0,
            attempt_timeout=0.05,
        )
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_retry_attempt_timeout(async_sdk):
    initial_time = time.monotonic()
    result = await async_sdk.models.completions('foo').tokenize(
        'slow-first-attempt',
        timeout=1,
    )
    retry_delta = time.monotonic() - initial_time

    assert result[0].text == 'retried'
    assert result[0].id == 2
    assert result[0].special is False
    assert retry_delta < 0.5


@pytest.mark.parametrize('attempt_timeout', [0, -1])
def test_retry_attempt_timeout_must_be_positive(attempt_timeout):
    with pytest.raises(ValueError, match='attempt_timeout must be greater than zero'):
        RetryPolicy(attempt_timeout=attempt_timeout)
