# pylint: disable=no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator
from typing import TYPE_CHECKING, TypeVar, cast

import grpc.aio
from yandex.cloud.ai.tts.v3.tts_pb2 import (
    ForceSynthesisEvent, StreamSynthesisRequest, StreamSynthesisResponse, SynthesisInput, SynthesisOptions
)
from yandex.cloud.ai.tts.v3.tts_service_pb2_grpc import SynthesizerStub

from yandex_ai_studio_sdk._client import AsyncCloudClient
from yandex_ai_studio_sdk._speechkit.enums import AudioFormat
from yandex_ai_studio_sdk._types.proto import SDKType
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync, run_sync_generator

from .config import TextToSpeechConfig
from .result import RequestDetails, TextToSpeechResult

if TYPE_CHECKING:
    # because grpc have a very funny type stubs which are not 100% synced with grpc itself
    EOFType = grpc.aio._EOFType
    EOF = EOFType()
else:
    EOF = grpc.aio.EOF
    EOFType = type(EOF)


class BaseTTSBidirectionalStream:
    """Bidirectional SpeechKit TTS API which allows to write requests and read synthesized result
    in realtime"""

    def __init__(
        self,
        *,
        sdk: SDKType,
        config: TextToSpeechConfig,
        timeout: float,
    ):
        self._sdk = sdk
        self._config = config
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._done_writing_flag = False
        self._done_writing_lock = asyncio.Lock()

        self.__call: grpc.aio.StreamStreamCall | None = None

    async def _get_call(self):
        if self.__call is not None:
            return self.__call

        async with self._lock:
            if self.__call is None:
                async with self._client.get_service_stub(SynthesizerStub, timeout=self._timeout) as stub:
                    self.__call = await self._client.stream_stream_call(stub.StreamSynthesis, timeout=self._timeout)
                    await self._send_stream_options()

        return self.__call

    async def _send_stream_options(self):
        assert self.__call
        assert self._lock.locked()

        c = self._config

        options = SynthesisOptions(
            loudness_normalization_type=c.loudness_normalization,  # type: ignore[arg-type]
            model=c.model or "",
            output_audio_spec=AudioFormat._to_proto(c.audio_format),
            pitch_shift=c.pitch_shift,
            role=c.role,
            speed=c.speed,
            voice=c.voice,
            volume=c.volume,
        )

        with self._client.with_sdk_error(SynthesizerStub):
            await self.__call.write(
                StreamSynthesisRequest(
                    options=options
                ),
            )

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    async def _write(self, input: str) -> None:
        """Write a input to be synthesized"""
        async with self._done_writing_lock:
            if self._done_writing_flag:
                raise RuntimeError(
                    f"stream {self.__class__.__name__} is closed for writing new inputs "
                    "after calling .done_writing()"
                )

            call = await self._get_call()

            with self._client.with_sdk_error(SynthesizerStub):
                request = StreamSynthesisRequest(
                    synthesis_input=SynthesisInput(text=input)
                )
                await call.write(request)

    async def _read(self) -> TextToSpeechResult | None:
        """Read chunk of synthesized result.

        Returns ``None`` in case of closed stream.
        """

        call = await self._get_call()

        with self._client.with_sdk_error(SynthesizerStub):
            response: StreamSynthesisResponse | EOFType = await call.read()
            if response == EOF:
                return None

            return TextToSpeechResult._from_proto(
                proto=cast(StreamSynthesisResponse, response),
                sdk=self._sdk,
                ctx=RequestDetails(model_config=self._config, timeout=self._timeout)
            )

    async def _gen(self) -> AsyncGenerator[TextToSpeechResult]:
        """Returns generator over all synthesized result parts."""

        chunk = await self._read()
        while chunk is not None:
            yield chunk
            chunk = await self._read()

    async def _done_writing(self) -> None:
        """Close the stream to tell to a server you done writing.

        Closing the stream will allow any iteration over this stream to exit.

        It is very important to close the stream to properly release resources.
        """

        async with self._done_writing_lock:
            call = await self._get_call()
            self._done_writing_flag = True
            with self._client.with_sdk_error(SynthesizerStub):
                await call.done_writing()

    async def _flush(self) -> None:
        """Send message to server to force synthesis with already given input"""

        call = await self._get_call()
        with self._client.with_sdk_error(SynthesizerStub):
            request = StreamSynthesisRequest(
                force_synthesis=ForceSynthesisEvent()
            )
            await call.write(request)


class AsyncTTSBidirectionalStream(BaseTTSBidirectionalStream, AsyncIterator[TextToSpeechResult]):
    __doc__ = BaseTTSBidirectionalStream.__doc__

    @doc_from(BaseTTSBidirectionalStream._write)
    async def write(self, input: str) -> None:
        await self._write(input)

    @doc_from(BaseTTSBidirectionalStream._read)
    async def read(self) -> TextToSpeechResult | None:
        return await self._read()

    async def __anext__(self) -> TextToSpeechResult:
        """Same as ``.read``, but makes AsyncTTSBidirectionalStream
        eligible to be used as AsyncIterator."""

        result = await self._read()
        if result is None:
            raise StopAsyncIteration
        return result

    @doc_from(BaseTTSBidirectionalStream._gen)
    async def gen(self) -> AsyncGenerator[TextToSpeechResult]:
        async for chunk in self._gen():
            yield chunk

    @doc_from(BaseTTSBidirectionalStream._done_writing)
    async def done_writing(self) -> None:
        await self._done_writing()

    @doc_from(BaseTTSBidirectionalStream._flush)
    async def flush(self) -> None:
        await self._flush()

    def __aiter__(self) -> AsyncIterator[TextToSpeechResult]:
        return self


class TTSBidirectionalStream(BaseTTSBidirectionalStream, Iterator[TextToSpeechResult]):
    __doc__ = BaseTTSBidirectionalStream.__doc__
    __write = run_sync(BaseTTSBidirectionalStream._write)
    __read = run_sync(BaseTTSBidirectionalStream._read)
    __gen = run_sync_generator(BaseTTSBidirectionalStream._gen)
    __done_writing = run_sync(BaseTTSBidirectionalStream._done_writing)
    __flush = run_sync(BaseTTSBidirectionalStream._flush)

    @doc_from(BaseTTSBidirectionalStream._write)
    def write(self, input: str) -> None:
        self.__write(input)

    @doc_from(BaseTTSBidirectionalStream._read)
    def read(self) -> TextToSpeechResult | None:
        return self.__read()

    def __next__(self) -> TextToSpeechResult:
        """Same as ``.read``, but makes TTSBidirectionalStream
        eligible to be used as Iterator."""

        result = self.__read()
        if result is None:
            raise StopIteration

        return result

    @doc_from(BaseTTSBidirectionalStream._gen)
    def gen(self) -> Generator[TextToSpeechResult]:
        yield from self.__gen()

    @doc_from(BaseTTSBidirectionalStream._done_writing)
    def done_writing(self) -> None:
        self.__done_writing()

    @doc_from(BaseTTSBidirectionalStream._flush)
    def flush(self) -> None:
        self.__flush()

    def __iter__(self) -> Iterator[TextToSpeechResult]:
        return self


TTSBidirectionalStreamTypeT = TypeVar('TTSBidirectionalStreamTypeT', bound=BaseTTSBidirectionalStream)
