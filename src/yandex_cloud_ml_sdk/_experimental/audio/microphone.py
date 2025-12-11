#!/usr/bin/env python3
"""
Experimental module for async audio data iterator from microphone;

To use it: ``pip install sounddevice numpy``
At Ubuntu also: ``sudo apt install libportaudio2``
At Windows and MacOS PortAudio will be installed automagically.

NB: AsyncMicrophone is not threadsafe!
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, cast

import numpy as np
import sounddevice as sd

try:
    from .utils import SENTINEL, Sentinel, choose_audio_device, float_to_pcm16
except ImportError:
    from utils import (  # type: ignore[no-redef,import-not-found,attr-defined,import-not-found]
        SENTINEL, Sentinel, choose_audio_device, float_to_pcm16
    )


IN_RATE = 24000
FRAME_MS = 20
IN_SAMPLES = int(IN_RATE * FRAME_MS / 1000)

DTYPE = 'float32'
QUEUE_ITEM_SIZE = IN_SAMPLES * 4  # size of float32 in queue
MAX_QUEUE_SIZE_BYTES = 1024 ** 3  # 1 GB
MAX_QUEUE_SIZE = MAX_QUEUE_SIZE_BYTES // QUEUE_ITEM_SIZE


class AsyncMicrophone:
    def __init__(
        self,
        *,
        device_id: int | None = None,
        samplerate: int = IN_RATE,
        blocksize: int = IN_SAMPLES,
    ):
        self._device_id = device_id
        self._samplerate = samplerate
        self._blocksize = blocksize

        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[np.ndarray | Sentinel] | None = None
        self._stream: sd.InputStream | None = None
        self._start_lock = asyncio.Lock()

    @property
    def queue_size(self) -> int:
        assert self._queue
        return self._queue.qsize()

    # pylint: disable=unused-argument
    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ):
        if self._loop and self._queue:
            # in case of full queue, it will generate a lot of errors into stderr
            # but will not interrupt the program
            self._loop.call_soon_threadsafe(self._queue.put_nowait, indata.copy())

    async def _start(self) -> None:
        async with self._start_lock:
            if self._loop:
                raise RuntimeError('cannot iterate over one microphone simultaneously')

            self._queue = asyncio.Queue(MAX_QUEUE_SIZE)
            self._loop = asyncio.get_running_loop()
            self._stream = sd.InputStream(
                device=self._device_id,
                samplerate=self._samplerate,
                channels=1,
                dtype=DTYPE,
                blocksize=self._blocksize,
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


async def main():
    """
    Just checking some edge-cases here and giving example of using microphone
    """
    # pylint: disable=import-outside-toplevel
    import wave

    device_id = choose_audio_device('in')

    can_stream_input = asyncio.Event()
    can_stream_input.set()

    mic = AsyncMicrophone(device_id=device_id)

    async def stop():
        await asyncio.sleep(2)
        print('stop')
        await mic.stop()

    asyncio.create_task(stop())
    # pylint: disable=no-member
    with wave.open('input.wav', 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(IN_RATE)

        async for pcm in mic:
            print(len(pcm))
            wf.writeframes(pcm)

        async for pcm in mic:
            print(len(pcm))
            wf.writeframes(pcm)


if __name__ == '__main__':
    asyncio.run(main())
