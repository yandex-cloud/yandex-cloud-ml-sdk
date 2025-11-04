#!/usr/bin/env python3
"""
Experimental module for async audio data iterator from microphone;

To use it: ``pip install sounddevice numpy``
At Ubuntu also: ``sudo apt install libportaudio2``
At Windows and MacOS PortAudio will be installed automagically.

NB: MicStreamer is not threadsafe!
"""
from __future__ import annotations

import asyncio
import pathlib
from collections.abc import AsyncIterator
from typing import Any, cast

import numpy as np
import sounddevice as sd

IN_RATE = 24000
FRAME_MS = 20
IN_SAMPLES = int(IN_RATE * FRAME_MS / 1000)


def float_to_pcm16(data: np.ndarray) -> bytes:
    data = np.clip(data, -1.0, 1.0)
    return (data * 32767).astype(np.int16).tobytes()


class Sentinel:
    pass


SENTINEL = Sentinel()


class AsyncMicrophone:
    def __init__(
        self,
        microphone_id: str | None
    ):
        self._microphone_id = microphone_id

        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[np.ndarray | Sentinel] | None = None
        self._stream: sd.InputStream | None = None
        self._start_lock = asyncio.Lock()

    # pylint: disable=unused-argument
    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ):
        if self._loop and self._queue:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, indata.copy())

    async def _start(self) -> None:
        async with self._start_lock:
            if self._loop:
                raise RuntimeError('cannot iterate over one microphone simultaneously')

            self._queue = asyncio.Queue()
            self._loop = asyncio.get_running_loop()
            self._stream = sd.InputStream(
                device=self._microphone_id,
                samplerate=IN_RATE,
                channels=1,
                dtype='float32',
                blocksize=IN_SAMPLES,
                callback=self._callback,
            )
            await self._loop.run_in_executor(None, self._stream.start)

    async def __aiter__(self) -> AsyncIterator[bytes]:
        await self._start()

        try:
            while True:
                if not self._queue:
                    break

                try:
                    indata = await self._queue.get()
                except asyncio.CancelledError:
                    break

                if indata is SENTINEL:
                    break

                indata = cast(np.ndarray, indata)
                pcm_16 = float_to_pcm16(indata)
                yield pcm_16
        finally:
            await self.stop()
            self._clear()

    async def stop(self):
        async with self._start_lock:
            if not self._loop or not self._queue or not self._stream:
                return

            if self._stream.active:
                await self._loop.run_in_executor(None, self._stream.stop)
                await self._queue.put(SENTINEL)

    def _clear(self):
        self._queue = None
        self._loop = None
        self._stream = None


def choose_microphone() -> int | None:
    microphones = [
        mic_data for mic_data in sd.query_devices()
        if mic_data.get('max_input_channels', 0) > 0
    ]
    if not microphones:
        raise RuntimeError('No microphones found')
    i = 0
    for i, mic_data in enumerate(microphones):
        print(f'[{i}] {mic_data["name"]}')

    raw_microphone_number = input(f'Type number from 0 to {i} (Nothing for system default): ')
    if not raw_microphone_number.strip():
        return None

    microphone_number = int(raw_microphone_number)
    return microphones[microphone_number]['index']


async def main():
    """
    Just checking some edge-cases here and giving example of using microphone
    """
    microphone_id = choose_microphone()

    can_stream_input = asyncio.Event()
    can_stream_input.set()

    mic = AsyncMicrophone(microphone_id)

    async def stop():
        await asyncio.sleep(2)
        print('stop')
        await mic.stop()

    with pathlib.Path('input.pcm').open('wb') as f_:
        asyncio.create_task(stop())
        async for pcm in mic:
            print(len(pcm))
            f_.write(pcm)

        async for pcm in mic:
            print(len(pcm))
            f_.write(pcm)


if __name__ == '__main__':
    asyncio.run(main())
