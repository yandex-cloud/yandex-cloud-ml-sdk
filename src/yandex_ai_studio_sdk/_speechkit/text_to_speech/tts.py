# pylint: disable=arguments-renamed,no-name-in-module,protected-access,redefined-builtin
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Generic, TypeVar

from typing_extensions import Self, override
from yandex.cloud.ai.tts.v3.tts_pb2 import DurationHint, Hints, UtteranceSynthesisRequest, UtteranceSynthesisResponse
from yandex.cloud.ai.tts.v3.tts_service_pb2_grpc import SynthesizerStub

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat as AudioFormat_
from yandex_ai_studio_sdk._speechkit.enums import LoudnessNormalization as LoudnessNormalization_
from yandex_ai_studio_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.model import ModelSyncMixin, ModelSyncStreamMixin
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync, run_sync_generator

from .bistream import AsyncTTSBidirectionalStream, TTSBidirectionalStream, TTSBidirectionalStreamTypeT
from .config import TextToSpeechConfig
from .result import RequestDetails, TextToSpeechResult

logger = get_logger(__name__)


class BaseTextToSpeech(
    Generic[TTSBidirectionalStreamTypeT],
    ModelSyncMixin[TextToSpeechConfig, TextToSpeechResult],
    ModelSyncStreamMixin[TextToSpeechConfig, TextToSpeechResult],
):
    """Text to Speech class which provides concrete methods for working with SpeechKit TTS API
    and incapsulates sintesis setting.
    """

    AudioFormat = AudioFormat_
    LoudnessNormalization = LoudnessNormalization_

    _config_type = TextToSpeechConfig
    _result_type = TextToSpeechResult
    _bistream_type: type[TTSBidirectionalStreamTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        loudness_normalization: UndefinedOrEnumWithUnknownInput[LoudnessNormalization_] | None = UNDEFINED,
        audio_format: UndefinedOrEnumWithUnknownInput[AudioFormat_] | None = UNDEFINED,
        model: UndefinedOr[str] | None = UNDEFINED,
        voice: UndefinedOr[str] | None = UNDEFINED,
        role: UndefinedOr[str] | None = UNDEFINED,
        speed: UndefinedOr[float] | None = UNDEFINED,
        volume: UndefinedOr[float] | None = UNDEFINED,
        pitch_shift: UndefinedOr[float] | None = UNDEFINED,
        duration_ms: UndefinedOr[int] | None = UNDEFINED,
        duration_min_ms: UndefinedOr[int] | None = UNDEFINED,
        duration_max_ms: UndefinedOr[int] | None = UNDEFINED,
        single_chunk_mode: UndefinedOr[bool] | None = UNDEFINED,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To return set value back to default, pass `None` value.

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
        :param duration_max_ms: Limit the maximum audio duration.
        :param single_chunk_mode: Automatically split long text to several utterances and bill accordingly.
            Some degradation in service quality is possible

        """

        return super().configure(
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
            single_chunk_mode=single_chunk_mode,
        )

    @override
    def __repr__(self) -> str:
        # Web Search doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    @override
    async def _run(
        self,
        input: str,
        *,
        timeout: float = 60,
    ) -> TextToSpeechResult:
        """Run a speech synthesis for given `text` and return joined result.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.speechkit.text_to_speech(audio_format='mp3')
        >>> search = search.configure(audio_format='WAV')

        :param text: Text to vocalize.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: synthesis result; joined in case of >1 chunks in synthesis response.
        """

        chunks = [chunk async for chunk in self._run_impl(input=input, timeout=timeout)]

        return self._result_type._from_proto_iterable(
            proto=chunks,
            sdk=self._sdk,
            ctx=RequestDetails(model_config=self.config, timeout=timeout)
        )

    @override
    async def _run_stream(
        self,
        input: str,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[TextToSpeechResult]:
        """Run a speech synthesis for given text at `input`; method have an iterator return.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.speechkit.text_to_speech(audio_format='mp3')
        >>> search = search.configure(audio_format='WAV')

        :param text: Text to vocalize.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: synthesis result; joined in case of >1 chunks in synthesis response.
        """

        async for proto in self._run_impl(input=input, timeout=timeout):
            yield self._result_type._from_proto(
                proto=proto,
                sdk=self._sdk,
                ctx=RequestDetails(model_config=self.config, timeout=timeout),
            )

    async def _run_impl(
        self,
        *,
        input: str,
        timeout: float,
    ) -> AsyncIterator[UtteranceSynthesisResponse]:
        c = self._config
        c._validate_run()

        output_audio_spec =  AudioFormat_._to_proto(c.audio_format)

        hints: list[Hints] = []
        _p = DurationHint.DurationHintPolicy
        for policy, hint_value in (
            (_p.EXACT_DURATION, c.duration_ms),
            (_p.MIN_DURATION, c.duration_min_ms),
            (_p.MAX_DURATION, c.duration_max_ms),
        ):
            if hint_value is None:
                continue

            hint = Hints(duration=DurationHint(policy=policy, duration_ms=hint_value))
            hints.append(hint)

        for hint_name in ('voice', 'speed', 'volume', 'role', 'pitch_shift'):
            hint_value = getattr(c, hint_name)
            if hint_value is None:
                continue
            hint = Hints(**{hint_name: hint_value})
            hints.append(hint)

        # NB: audio_template hint is not used

        request = UtteranceSynthesisRequest(
            model=c.model or '',
            text=input,
            text_template=None,
            loudness_normalization_type=c.loudness_normalization,  # type: ignore[arg-type]
            hints=hints,
            output_audio_spec=output_audio_spec,
            unsafe_mode=not c.single_chunk_mode,
        )
        async with self._client.get_service_stub(SynthesizerStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.UtteranceSynthesis,
                request,
                timeout=timeout,
                expected_type=UtteranceSynthesisResponse,
            ):
                yield response

    def create_bistream(self, *, timeout: float = 10 * 60) -> TTSBidirectionalStreamTypeT:
        """Creates a bidirectional stream object for using
        `Yandex SpeechKit Streaming synthesis <https://yandex.cloud/en/docs/speechkit/tts/api/tts-streaming>`_.

        :param timeout: GRPC timeout in seconds that defines the maximum lifetime of the entire stream.
            The timeout countdown begins from the moment of the first stream interaction.
        """

        self._config._validate_bistream()

        return self._bistream_type(
            sdk=self._sdk,
            config=self._config,
            timeout=timeout
        )



class AsyncTextToSpeech(BaseTextToSpeech[AsyncTTSBidirectionalStream]):
    _bistream_type = AsyncTTSBidirectionalStream

    @doc_from(BaseTextToSpeech._run)
    async def run(
        self,
        input: str,
        *,
        timeout: float = 60
    ) -> TextToSpeechResult:
        return await self._run(input=input, timeout=timeout)

    async def run_stream(
        self,
        input: str,
        *,
        timeout: float = 60
    ) -> AsyncIterator[TextToSpeechResult]:
        async for chunk in self._run_stream(input=input, timeout=timeout):
            yield chunk


@doc_from(BaseTextToSpeech)
class TextToSpeech(BaseTextToSpeech[TTSBidirectionalStream]):
    _bistream_type = TTSBidirectionalStream
    __run = run_sync(BaseTextToSpeech._run)
    __run_stream = run_sync_generator(BaseTextToSpeech._run_stream)

    @doc_from(BaseTextToSpeech._run)
    def run(
        self,
        input: str,
        *,
        timeout: float = 60
    ):
        return self.__run(input=input, timeout=timeout)

    @doc_from(BaseTextToSpeech._run_stream)
    def run_stream(
        self,
        input: str,
        *,
        timeout: float = 60
    ) -> Iterator[TextToSpeechResult]:
        yield from self.__run_stream(input=input, timeout=timeout)


TextToSpeechTypeT = TypeVar('TextToSpeechTypeT', bound=BaseTextToSpeech)
