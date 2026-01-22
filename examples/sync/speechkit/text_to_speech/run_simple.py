#!/usr/bin/env python3

from __future__ import annotations

import numpy as np
from sounddevice import OutputStream

from yandex_ai_studio_sdk import AIStudio
from yandex_ai_studio_sdk._experimental.audio.utils import choose_audio_device

SAMPLERATE = 44100


def convert(data: bytes):
    audio_int16 = np.frombuffer(data, dtype=np.int16)
    audio_normalized = audio_int16.astype(np.float32) / 32768.0
    return audio_normalized


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
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

    query = input('Enter the text to synthesize: ')
    if not query.strip():
        gpt = sdk.chat.completions('aliceai-llm')
        gpt = gpt.configure(max_tokens=100)
        gpt_result = gpt.run("Сгенерируй сказку на 500 символов про Yandex Cloud AI Studio")
        query = gpt_result.text
        print(f"Generated {len(query)} characters text")

    with OutputStream(samplerate=SAMPLERATE, device=output_device_id, channels=1) as out:
        # Basic method - .run_stream, which yields result chunk by chunk
        for partial_result in tts.run_stream(query):
            print(f'Chunk [{partial_result.start_ms}, {partial_result.end_ms}] ms: {partial_result.text}')
            out.write(convert(partial_result.data))

        # There is also helper-method .run which returns already joined result
        result = tts.run(query)
        print(f"Joined result [{result.start_ms}, {result.end_ms}]: {result.text}")
        out.write(convert(result.data))

        # But you still could introspect joined chunks of joined result
        for i, chunk in enumerate(result.chunks):
            print(f'Chunk {i}: {chunk.length_ms=}, {chunk.size_bytes=}')


if __name__ == '__main__':
    main()
