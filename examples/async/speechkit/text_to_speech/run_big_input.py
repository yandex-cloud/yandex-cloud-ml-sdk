#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncYCloudML
from yandex_ai_studio_sdk._experimental.audio.out import AsyncAudioOut
from yandex_ai_studio_sdk._experimental.audio.utils import choose_audio_device

SAMPLERATE = 44100


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
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
    # we need to use bistream because tts.run/run_stream have limitations on input length
    # NB: bistream timeout is defining max lifetime for WHOLE STREAM
    bistream = tts.create_bistream(timeout=60 * 10)

    gpt = sdk.chat.completions('aliceai-llm')
    gpt = gpt.configure(max_tokens=100)

    async for chunk in gpt.run_stream(
        "Сгенерируй сказку на 1000 символов про Yandex Cloud AI Studio, без служебных символов"
    ):
        if delta := chunk[0].delta:  # type: ignore[attr-defined]
            await bistream.write(delta)
            print(f"Generated {len(delta)} characters chunk")

    # in this case .flush is redundant because we will call .done_writing afterwards
    await bistream.flush()

    # We need to tell to a server that we are finished writing;
    # Server will send the rest of output and finish the stream, which
    # will release async for loop at bottom of this file
    await bistream.done_writing()

    try:
        async with AsyncAudioOut(device_id=output_device_id, samplerate=SAMPLERATE) as out:
            # Here we are consuming TTS output via async iterator interface:
            async for partial_result in bistream:
                print(f'Chunk [{partial_result.start_ms}, {partial_result.end_ms}] ms: {partial_result.text}')
                await out.write(partial_result.data)

    except asyncio.CancelledError:
        # processing graceful exit with KeyboardInterrupt
        pass
    finally:
        # if not finished, we are clearing audio out buffer
        await out.clear()


if __name__ == '__main__':
    asyncio.run(main())
