#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._experimental.audio.out import AsyncAudioOut
from yandex_cloud_ml_sdk._experimental.audio.utils import choose_audio_device


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
        audio_format='PCM16(44100)'
    )

    query = input('Enter the text to synthesize: ')
    if not query.strip():
        query = 'Yandex Cloud'

    async with AsyncAudioOut(device_id=output_device_id, samplerate=44100) as out:
        async for chunk in tts.run_chunked(query):
            await out.write(chunk.data)
            print(chunk)


if __name__ == '__main__':
    asyncio.run(main())
