# pylint: disable=no-name-in-module,invalid-overridden-method
from __future__ import annotations

import pytest
from yandex.cloud.ai.tts.v3.tts_pb2 import AudioChunk, StreamSynthesisRequest, StreamSynthesisResponse, TextChunk
from yandex.cloud.ai.tts.v3.tts_service_pb2_grpc import SynthesizerServicer, add_SynthesizerServicer_to_server


@pytest.fixture
def servicers():
    class SynthesizerServicerImpl(SynthesizerServicer):
        def StreamSynthesis(self, request_iterator, context):
            requests = list(request_iterator)
            assert all(isinstance(r, StreamSynthesisRequest) for r in requests)
            first, second, third = requests

            assert first.HasField('options')
            assert second.HasField('synthesis_input')
            assert third.HasField('force_synthesis')

            yield StreamSynthesisResponse(
                audio_chunk=AudioChunk(data=b'foo'),
                text_chunk=TextChunk(text='bar'),
                length_ms=10,
                start_ms=1,
            )

    return [
        (SynthesizerServicerImpl(), add_SynthesizerServicer_to_server),
    ]


@pytest.mark.asyncio
async def test_bistream(async_sdk):
    tts = async_sdk.speechkit.tts()
    stream = tts.create_bistream()

    await stream.write('foo')
    await stream.flush()
    await stream.done_writing()
    results = [r async for r in stream]
    result = results[0]
    assert result

    assert result.data == b'foo'
    assert result.text == 'bar'
    assert result.start_ms == 1
    assert result.end_ms == 11
