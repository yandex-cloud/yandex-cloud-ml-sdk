#!/usr/bin/env python3
from __future__ import annotations

from typing import Literal

import numpy as np
import sounddevice as sd


class Sentinel:
    pass


SENTINEL = Sentinel()


def float_to_pcm16(data: np.ndarray) -> bytes:
    data = np.clip(data, -1.0, 1.0)
    return (data * 32767).astype(np.int16).tobytes()


def choose_audio_device(kind: Literal['in', 'out']) -> int | None:
    key = 'max_input_channels' if kind == 'in' else 'max_output_channels'

    devices = [
        data for data in sd.query_devices()
        if data.get(key, 0) > 0
    ]
    if not devices:
        raise RuntimeError(f'No "{kind}" devices found')
    i = 0
    for i, data in enumerate(devices):
        print(f'[{i}] {data["name"]}')

    raw_device_number = input(f'Type "{kind}" device number from 0 to {i} (Nothing for system default): ')
    if not raw_device_number.strip():
        return None

    device_number = int(raw_device_number)
    return devices[device_number]['index']
