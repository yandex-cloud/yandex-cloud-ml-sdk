#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._experimental.audio.out import AsyncAudioOut
from yandex_cloud_ml_sdk._experimental.audio.utils import choose_audio_device

SAMPLERATE = 44100


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    output_device_id = choose_audio_device('out')

    tts = sdk.speechkit.text_to_speech(
        voice='kirill',
        audio_format=f'PCM16({SAMPLERATE})',
    )
    # you can configure TTS object after creation
    tts = tts.configure(
        # alternative way to specify audio_format
        audio_format=tts.AudioFormat.PCM16(SAMPLERATE),
        loudness_normalization=tts.LoudnessNormalization.LUFS,
        speed=1.5,
    )

    query = input('Enter the text to synthesize: ')
    if not query.strip():
        gpt = sdk.chat.completions('aliceai-llm')
        gpt = gpt.configure(max_tokens=100)
        gpt_result = await gpt.run("Сгенерируй сказку на 500 символов про Yandex Cloud AI Studio")
        query = gpt_result.text
        print(f"Generated {len(query)} characters text")

    async with AsyncAudioOut(device_id=output_device_id, samplerate=SAMPLERATE) as out:
        # Basic method - .run_stream, which yields result chunk by chunk
        async for partial_result in tts.run_stream(query):
            print(f'Chunk [{partial_result.start_ms}, {partial_result.end_ms}] ms: {partial_result.text}')
            await out.write(partial_result.data)

        # There is also helper-method .run which returns already joined result
        result = await tts.run(query)
        print(f"Joined result [{result.start_ms}, {result.end_ms}]: {result.text}")
        await out.write(result.data)

        # But you still could introspect joined chunks of joined result
        for i, chunk in enumerate(result.chunks):
            print(f'Chunk {i}: {chunk.length_ms=}, {chunk.size_bytes=}')



if __name__ == '__main__':
    asyncio.run(main())
