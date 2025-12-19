from __future__ import annotations

import io
import wave


def pcm16_to_wav(pcm_data: bytes, sample_rate: int) -> bytes:
    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, 'wb') as wav_file:
        # pylint: disable=no-member
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

    return wav_buffer.getvalue()
