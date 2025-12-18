from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._speechkit.enums import PCM16
from yandex_cloud_ml_sdk._types.misc import UNDEFINED


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_tts_run(async_sdk: AsyncYCloudML) -> None:
    tts = async_sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format='PCM16(44100)',
    )
    query = 'test test test'

    result = await tts.run(query)

    assert result.text == query
    assert isinstance(
        # pylint: disable=protected-access
        result._request_details.model_config.audio_format,
        PCM16
    )
    assert len(result.chunks) == 1

    assert result.data == result.chunks[0].data
    assert result.end_ms == result.chunks[0].end_ms


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_tts_long_run(async_sdk: AsyncYCloudML) -> None:
    tts = async_sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format='PCM16(44100)',
    )
    query = 'test ' * 100

    result = await tts.run(query)

    assert result.text.strip() == query.strip()
    assert isinstance(
        # pylint: disable=protected-access
        result._request_details.model_config.audio_format,
        PCM16
    )
    assert len(result.chunks) > 1

    assert result.data.startswith(result.chunks[0].data)
    assert result.data.endswith(result.chunks[-1].data)
    assert result.end_ms == result.chunks[-1].end_ms


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_tts_stream_run(async_sdk: AsyncYCloudML) -> None:
    tts = async_sdk.speechkit.text_to_speech()
    query = 'test ' * 100

    chunks = [chunk async for chunk in tts.run_stream(query)]

    assert len(chunks) > 1


@pytest.mark.asyncio
async def test_tts_configure(async_sdk: AsyncYCloudML) -> None:
    async_sdk.speechkit.text_to_speech(duration_max_ms=1, duration_min_ms=2)
    async_sdk.speechkit.text_to_speech(duration_ms=10)

    with pytest.raises(ValueError):
        async_sdk.speechkit.text_to_speech(duration_ms=10, duration_max_ms=123)

    format_ = async_sdk.speechkit.text_to_speech(audio_format='PCM16(10)').config.audio_format

    assert isinstance(format_, PCM16)
    assert format_.sample_rate_hertz == 10


@pytest.mark.parametrize('audio_format', ['mp3', 'wav', 'ogg_opus', UNDEFINED, 'PCM16(44100)'])
@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_tts_result_repr(
    async_sdk: AsyncYCloudML,
    audio_format: str,
) -> None:
    tts = async_sdk.speechkit.text_to_speech(
        audio_format=audio_format
    )
    query = 'test test test'

    result = await tts.run(query)

    # pylint: disable=protected-access
    html = result._repr_html_()
    assert isinstance(html, str)
