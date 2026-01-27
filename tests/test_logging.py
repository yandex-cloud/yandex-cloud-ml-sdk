# pylint: disable=no-name-in-module,invalid-overridden-method
from __future__ import annotations

import logging

import pytest
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Token
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    CompletionResponse, TokenizeResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationServiceServicer, TokenizerServiceServicer, add_TextGenerationServiceServicer_to_server,
    add_TokenizerServiceServicer_to_server
)


@pytest.fixture
def servicers():
    class TextGenerationServicer(TextGenerationServiceServicer):
        def Completion(self, request, context):
            context.set_trailing_metadata((
                ('key', 'value'),
            ))
            yield CompletionResponse(
                alternatives=[],
                usage=None,
                model_version='111'
            )

    class TokenizerService(TokenizerServiceServicer):
        def TokenizeCompletion(self, request, context):
            context.set_trailing_metadata((
                 ('key', 'value'),
            ))
            return TokenizeResponse(
                tokens=[Token(id=1, text="abc", special=True)],
                model_version="222"
            )

    return [
        (TextGenerationServicer(), add_TextGenerationServiceServicer_to_server),
        (TokenizerService(), add_TokenizerServiceServicer_to_server),
    ]


@pytest.mark.asyncio
async def test_logging_unary_unary(async_sdk, caplog):
    # sometimes there are strange asyncio+grpc ERROR log message about shutdown
    # and I'm too lazy to write a code here about selecting this test target log message
    # instead of just records[0]
    caplog.set_level(50)
    caplog.set_level(logging.DEBUG, logger="yandex_ai_studio_sdk")

    result = await async_sdk.models.completions('foo').tokenize('bar')
    assert result[0].text == 'abc'
    assert result[0].id == 1
    assert result[0].special is True

    assert caplog.records
    record = caplog.records[0]
    assert record.args
    metadata = record.args[-1]
    assert isinstance(metadata, dict)
    assert metadata['key'] == 'value'


@pytest.mark.asyncio
async def test_logging_unary_stream(async_sdk, caplog):
    # sometimes there are strange asyncio+grpc ERROR log message about shutdown
    # and I'm too lazy to write a code here about selecting this test target log message
    # instead of just records[0]
    caplog.set_level(50)
    caplog.set_level(logging.DEBUG, logger="yandex_ai_studio_sdk")
    result = await async_sdk.models.completions('foo').run('bar')
    assert result is not None
    assert not result.alternatives

    assert caplog.records
    record = caplog.records[0]
    assert record.args
    metadata = record.args[-1]
    assert isinstance(metadata, dict)
    assert metadata['key'] == 'value'
