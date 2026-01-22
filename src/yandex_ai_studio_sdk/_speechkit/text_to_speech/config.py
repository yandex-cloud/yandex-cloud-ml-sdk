from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union, cast

from typing_extensions import Self, override

from yandex_ai_studio_sdk._exceptions import AIStudioConfigurationError
from yandex_ai_studio_sdk._speechkit.enums import PCM16, AudioFormat, LoudnessNormalization
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownAlias, EnumWithUnknownInput, ProtoBasedEnum
from yandex_ai_studio_sdk._types.model_config import BaseModelConfig


@dataclass(frozen=True)
class TextToSpeechConfig(BaseModelConfig):
    #: Specifies type of loudness normalization.
    #: Default: `LUFS`.
    loudness_normalization: EnumWithUnknownAlias[LoudnessNormalization] | None = None
    #: Specifies output audio format. Default: 22050Hz, linear 16-bit signed little-endian PCM, with WAV header.
    audio_format: EnumWithUnknownAlias[AudioFormat] | None = None
    #: The name of the TTS model to use for synthesis. Currently should be empty. Do not use it.
    model: str | None = None
    #: The voice to use for speech synthesis.
    voice: str | None = None
    #: The role or speaking style. Can be used to specify pronunciation character for the speaker.
    role: str | None = None
    #: Speed multiplier (default: 1.0).
    speed: float | None = None
    #: Volume adjustment:
    #: * For `MAX_PEAK`: range is (0, 1], default 0.7.
    #: * For `LUFS`: range is [-145, 0), default -19.
    volume: float | None = None
    #: Pitch adjustment, in Hz, range [-1000, 1000], default 0.
    pitch_shift: float | None = None
    #: Limit audio duration to exact value
    duration_ms: int | None = None
    #: Limit the minimum audio duration
    duration_min_ms: int | None = None
    #: Limit the maximum audio duration
    duration_max_ms: int | None = None

    #: :meta private:
    #: Automatically split long text to several utterances and bill accordingly.
    #: Some degradation in service quality is possible
    single_chunk_mode: bool = False

    @override
    def _replace(self, **kwargs: Any) -> Self:
        enum: type[ProtoBasedEnum]
        for field, enum in (
            ('loudness_normalization', LoudnessNormalization),
            ('audio_format', AudioFormat),
        ):
            value = cast(Union[EnumWithUnknownInput, None], kwargs.get(field))
            if value is None:
                continue

            kwargs[field] = enum._coerce(value)

        return super()._replace(**kwargs)

    @override
    def _validate_configure(self) -> None:
        if (
            self.duration_ms is not None and (
                self.duration_max_ms is not None or
                self.duration_min_ms is not None
            )
        ):
            raise AIStudioConfigurationError(
                'it is forbidden to use duration_ms config option '
                'with duration_max_ms or duration_min_ms'
            )

        if isinstance(self.audio_format, PCM16) and self.audio_format.channels != 1:
            raise AIStudioConfigurationError(
                "PCM16 audio format can't have channels number other than 1 in text_to_speech"
            )

    def _validate_bistream(self) -> None:
        unsupported_options = [
            "duration_max_ms",
            "duration_min_ms",
            "duration_ms",
            "single_chunk_mode"
        ]
        defined_unsupported_options = [
            option_name
            for option_name in unsupported_options
            if getattr(self, option_name)
        ]
        if defined_unsupported_options:
            raise AIStudioConfigurationError(
                f"bistream doesn't support config options {unsupported_options}, "
                f"but you have {defined_unsupported_options} installed"
            )
