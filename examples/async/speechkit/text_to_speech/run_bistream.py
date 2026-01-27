#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._experimental.audio.out import AsyncAudioOut
from yandex_ai_studio_sdk._experimental.audio.utils import choose_audio_device

SAMPLERATE = 44100


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    ).setup_default_logging()

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

    gpt = sdk.chat.completions('aliceai-llm')
    gpt = gpt.configure(max_tokens=100)

    async def make_input_stream(writer):
        async for chunk in gpt.run_stream(
            "Сгенерируй сказку на 1000 символов про Yandex Cloud AI Studio, без служебных символов"
        ):
            if delta := chunk[0].delta:
                await writer.write(delta)
                print(f"Generated {len(delta)} characters chunk")

        # We need to tell to a server that we are finished writing;
        # Server will send the rest of output and finish the stream, which
        # will release async for loop at bottom of this file
        await writer.done_writing()

    # NB: bistream timeout is defining max lifetime for WHOLE STREAM
    bistream = tts.create_bistream(timeout=60 * 10)

    # we are creating asyncio task which will call bistream.write in the background
    input_task = asyncio.create_task(make_input_stream(bistream))

    try:
        async with AsyncAudioOut(device_id=output_device_id, samplerate=SAMPLERATE) as out:
            # Here we are consuming TTS output via async iterator interface:
            async for partial_result in bistream:
                print(f'Chunk [{partial_result.start_ms}, {partial_result.end_ms}] ms: {partial_result.text}')
                await out.write(partial_result.data)

        await input_task
    except asyncio.CancelledError:
        # processing graceful exit with KeyboardInterrupt
        pass
    finally:
        # if not finished, we are cancelling writer task and clearing audio out buffer
        input_task.cancel()
        await out.clear()


if __name__ == '__main__':
    asyncio.run(main())
