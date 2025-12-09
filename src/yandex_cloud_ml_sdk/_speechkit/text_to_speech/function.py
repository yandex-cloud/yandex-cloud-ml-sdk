from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._speechkit.enums import AudioFormat, LoudnessNormalization
from yandex_cloud_ml_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .tts import AsyncTextToSpeech, TextToSpeech, TextToSpeechTypeT


class BaseTextToSpeechFunction(BaseModelFunction[TextToSpeechTypeT]):
    """Text to Speech function for creating synthesis object which provides
    methods for invoking voice synthesizing.
    """

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
        *,
        loudness_normalization: UndefinedOrEnumWithUnknownInput[LoudnessNormalization] = UNDEFINED,
        audio_format: UndefinedOrEnumWithUnknownInput[AudioFormat] = UNDEFINED,
        model: UndefinedOr[str] = UNDEFINED,
        voice: UndefinedOr[str] = UNDEFINED,
        role: UndefinedOr[str] = UNDEFINED,
        speed: UndefinedOr[float] = UNDEFINED,
        volume: UndefinedOr[float] = UNDEFINED,
        pitch_shift: UndefinedOr[float] = UNDEFINED,
        duration_ms: UndefinedOr[int] = UNDEFINED,
        duration_min_ms: UndefinedOr[int] = UNDEFINED,
        duration_max_ms: UndefinedOr[int] = UNDEFINED,
    ) -> TextToSpeechTypeT:
        """
        Creates TextToSpeech object with provides methods for voice synthesizing.

        To learn more about parameters and their formats and possible values,
        refer to
        `TTS documentation <https://yandex.cloud/docs/speechkit/stt>`_

        :param loudness_normalization: Specifies type of loudness normalization.
            Default: `LUFS`.
        :param audio_format: Specifies output audio format.
            Default: 22050Hz, linear 16-bit signed little-endian PCM, with WAV header.
        :param model: The name of the TTS model to use for synthesis.
            Currently should be empty. Do not use it.
        :param voice: The voice to use for speech synthesis.
        :param role: The role or speaking style. Can be used to specify pronunciation character for the speaker.
        :param speed: Speed multiplier (default: 1.0).
        :param volume: Volume adjustment:
            * For `MAX_PEAK`: range is (0, 1], default 0.7.
            * For `LUFS`: range is [-145, 0), default -19.
        :param pitch_shift: Pitch adjustment, in Hz, range [-1000, 1000], default 0.
        :param duration_ms: Limit audio duration to exact value.
        :param duration_min_ms: Limit the minimum audio duration.
        :param duration_max_ms: Limit the maximum audio duration
        """

        tts = self._model_type(sdk=self._sdk, uri='<speechkit>')

        return tts.configure(
            loudness_normalization=loudness_normalization,
            audio_format=audio_format,
            model=model,
            voice=voice,
            role=role,
            speed=speed,
            volume=volume,
            pitch_shift=pitch_shift,
            duration_ms=duration_ms,
            duration_min_ms=duration_min_ms,
            duration_max_ms=duration_max_ms,
        )


@doc_from(BaseTextToSpeechFunction)
class TextToSpeechFunction(BaseTextToSpeechFunction[TextToSpeech]):
    _model_type = TextToSpeech


@doc_from(BaseTextToSpeechFunction)
class AsyncTextToSpeechFunction(BaseTextToSpeechFunction[AsyncTextToSpeech]):
    _model_type = AsyncTextToSpeech
