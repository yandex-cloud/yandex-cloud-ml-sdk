from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.tts.v3.tts_pb2 import UtteranceSynthesisResponse

from yandex_cloud_ml_sdk._types.result import BaseProtoResult, SDKType


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
class TextToSpeechResult(BaseProtoResult[UtteranceSynthesisResponse]):
    """A class representing the partially parsed result of a Web search request
    with XML format.
    """

    chunks: tuple[TextToSpeechChunk, ...]

    # NB: classmethod and override in opposite order breaking Jedi autocompletion
    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: UtteranceSynthesisResponse, sdk: SDKType) -> Self:
        chunk = TextToSpeechChunk(
            data=proto.audio_chunk.data,
            text=proto.text_chunk.text,
            start_ms=proto.start_ms,
            length_ms=proto.length_ms,
        )
        return cls(
            chunks=(chunk, )
        )

    @classmethod
    # pylint: disable-next=unused-argument
    def _from_proto_iterable(cls, *, proto: Iterable[UtteranceSynthesisResponse], sdk: SDKType) -> Self:
        chunks = (
            TextToSpeechChunk(
                data=p.audio_chunk.data,
                text=p.text_chunk.text,
                start_ms=p.start_ms,
                length_ms=p.length_ms,
            ) for p in proto
        )
        return cls(
            chunks=tuple(chunks)
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
