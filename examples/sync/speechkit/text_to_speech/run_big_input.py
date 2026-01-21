#!/usr/bin/env python3

from __future__ import annotations

import numpy as np
from sounddevice import OutputStream

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk._experimental.audio.utils import choose_audio_device

SAMPLERATE = 44100


def convert(data: bytes):
    audio_int16 = np.frombuffer(data, dtype=np.int16)
    audio_normalized = audio_int16.astype(np.float32) / 32768.0
    return audio_normalized


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
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

    for chunk in gpt.run_stream(
        "Сгенерируй сказку на 1000 символов про Yandex Cloud AI Studio, без служебных символов"
    ):
        if delta := chunk[0].delta:  # type: ignore[attr-defined]
            bistream.write(delta)
            print(f"Generated {len(delta)} characters chunk")

    # in this case .flush is redundant because we will call .done_writing afterwards
    bistream.flush()

    # We need to tell to a server that we are finished writing;
    # Server will send the rest of output and finish the stream, which
    # will release for loop at bottom of this file
    bistream.done_writing()

    try:
        with OutputStream(samplerate=SAMPLERATE, device=output_device_id, channels=1) as out:
            # Here we are consuming TTS output via iterator interface:
            for partial_result in bistream:
                print(f'Chunk [{partial_result.start_ms}, {partial_result.end_ms}] ms: {partial_result.text}')

                # NB out.write is blocking call and bistream could raise a timeout inside of iteration
                # because of slow output, but for demonstration purposes it is okay I guess
                out.write(convert(partial_result.data))
    finally:
        # if not finished, we are clearing audio out buffer
        out.close()


if __name__ == '__main__':
    main()
