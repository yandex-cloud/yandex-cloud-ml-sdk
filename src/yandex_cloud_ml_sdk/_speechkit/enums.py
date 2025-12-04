# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

import re
from typing import Never

from yandex.cloud.ai.tts.v3.tts_pb2 import ContainerAudio

from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum, UnknownEnumValue


class PCM16(UnknownEnumValue['AudioFormat']):
    def __new__(cls, sample_rate_hertz: int, channels: int):
        return super().__new__(cls, enum_type=AudioFormat, name='PCM16', value=-1)

    def __init__(self, sample_rate_hertz: int, channels: int):
        super().__init__(
            enum_type=AudioFormat,
            name='PCM16',
            value=-1
        )
        self._sample_rate_hertz = sample_rate_hertz
        self._channels = channels

    @property
    def sample_rate_hertz(self) -> int:
        return self._sample_rate_hertz

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def value(self) -> Never:
        raise RuntimeError("PCM16 can't be used with a value")

    def __str__(self) -> str:
        return (
            f'{self._enum_type.__name__}'
            f'.{self.__class__.__name__}'
            f'({self.sample_rate_hertz!r}, channels={self.channels!r})'
        )

    def __eq__(self, other) -> bool:
        if not super().__eq__(other):
            return False

        assert isinstance(other, PCM16)
        return (
            other.sample_rate_hertz == self.sample_rate_hertz and
            other.channels == self.channels
        )

    def __hash__(self) -> int:
        return hash((self._sample_rate_hertz, self._value))


class AudioFormat(ProtoBasedEnum):
    __proto_enum_type__ = ContainerAudio.ContainerAudioType
    __common_prefix__ = ''
    __unspecified_name__ = 'CONTAINER_AUDIO_TYPE_UNSPECIFIED'
    __pcm16_re__ = re.compile(
        r'(?:LINEAR16_PCM|PCM16)\((?P<sample_rate_hertz>\d+)(?:,[ ]?(?P<channels>\d+))?\)$'
    )

    __aliases__ = {
        'OPUS': 'OGG_OPUS',
    }

    MP3 = ContainerAudio.ContainerAudioType.MP3
    WAV = ContainerAudio.ContainerAudioType.WAV
    OGG_OPUS = ContainerAudio.ContainerAudioType.OGG_OPUS

    @classmethod
    def PCM16(cls, sample_rate_hertz: int, channels: int = 1) -> PCM16:
        return PCM16(sample_rate_hertz, channels)

    @classmethod
    def _coerce(
        cls: type[AudioFormat],
        value: EnumWithUnknownInput[AudioFormat],
    ) -> EnumWithUnknownAlias[AudioFormat]:
        if isinstance(value, str):
            # pylint: disable-next=no-member
            if match := cls.__pcm16_re__.match(value):
                sample_rate_hertz, channels = match.groups()
                return cls.PCM16(
                    sample_rate_hertz=int(sample_rate_hertz),
                    channels=int(channels) if channels else 1
                )

        return super()._coerce(value)

    @classmethod
    def _get_available(cls) -> tuple[str, ...]:
        return super()._get_available() + ('PCM16(<int>)', 'PCM16(<int>, <int>)')
