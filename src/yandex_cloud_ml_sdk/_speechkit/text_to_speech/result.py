from __future__ import annotations

import base64
from collections.abc import Iterable
from dataclasses import dataclass, field

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.tts.v3.tts_pb2 import UtteranceSynthesisResponse

from yandex_cloud_ml_sdk._speechkit.enums import PCM16, AudioFormat
from yandex_cloud_ml_sdk._speechkit.utils import pcm16_to_wav
from yandex_cloud_ml_sdk._types.request import RequestDetails
from yandex_cloud_ml_sdk._types.result import BaseProtoModelResult, SDKType

from .config import TextToSpeechConfig


@dataclass(frozen=True)
class TextToSpeechChunk:
    data: bytes
    text: str
    start_ms: int
    length_ms: int

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.length_ms

    @property
    def size_bytes(self) -> int:
        return len(self.data)

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}'
            '<'
            f'data=b"...", '
            f'text={self.text!r}, '
            f'segment=[{self.start_ms}, {self.end_ms}], '
            f'length_ms={self.length_ms}, '
            f'size_bytes={self.size_bytes}'
            '>'
        )

    def __repr__(self) -> str:
        return self.__str__()


@dataclass(frozen=True)
class TextToSpeechResult(BaseProtoModelResult[UtteranceSynthesisResponse, RequestDetails[TextToSpeechConfig]]):
    """A class representing the partially parsed result of a Web search request
    with XML format.
    """

    chunks: tuple[TextToSpeechChunk, ...]
    _request_details: RequestDetails[TextToSpeechConfig] = field(repr=False)

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: UtteranceSynthesisResponse, sdk: SDKType, ctx: RequestDetails[TextToSpeechConfig]) -> Self:
        chunk = TextToSpeechChunk(
            data=proto.audio_chunk.data,
            text=proto.text_chunk.text,
            start_ms=proto.start_ms,
            length_ms=proto.length_ms,
        )
        return cls(
            chunks=(chunk, ),
            _request_details=ctx,
        )

    @classmethod
    def _from_proto_iterable(
        cls,
        *,
        proto: Iterable[UtteranceSynthesisResponse],
        # pylint: disable-next=unused-argument
        sdk: SDKType,
        ctx: RequestDetails[TextToSpeechConfig]
    ) -> Self:
        chunks = (
            TextToSpeechChunk(
                data=p.audio_chunk.data,
                text=p.text_chunk.text,
                start_ms=p.start_ms,
                length_ms=p.length_ms,
            ) for p in proto
        )
        return cls(
            chunks=tuple(chunks),
            _request_details=ctx
        )


    @property
    def data(self) -> bytes:
        return b''.join(chunk.data for chunk in self.chunks)

    @property
    def text(self) -> str:
        return ' '.join(chunk.text for chunk in self.chunks)

    @property
    def start_ms(self) -> int:
        return self.chunks[0].start_ms

    @property
    def length_ms(self) -> int:
        return sum(chunk.length_ms for chunk in self.chunks)

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.length_ms

    @property
    def size_bytes(self) -> int:
        return sum(chunk.size_bytes for chunk in self.chunks)

    @property
    def audio_format(self) -> AudioFormat:
        return self._request_details.model_config.audio_format

    def _repr_html_(self) -> str | None:
        data = self.data
        mime_type: str
        if isinstance(self.audio_format, PCM16):
            sample_rate = self.audio_format.sample_rate_hertz
            data = pcm16_to_wav(self.data, sample_rate)
            mime_type = 'audio/wav'
        else:
            mime_type = {
                AudioFormat.WAV: 'audio/wav',
                AudioFormat.MP3: 'audio/mpeg',
                AudioFormat.OGG_OPUS: 'audio/ogg'
            }.get(self.audio_format)
            if not mime_type:
                return None

        b64 = base64.b64encode(data).decode('ascii')

        html = f'''
        <audio controls style="width: 100%;">
          <source src="data:{mime_type};base64,{b64}" type="{mime_type}">
          Your browser does not support the audio element..
        </audio>
        '''
        return html
