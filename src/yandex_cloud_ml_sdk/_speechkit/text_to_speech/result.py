from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.tts.v3.tts_pb2 import UtteranceSynthesisResponse

from yandex_cloud_ml_sdk._types.result import BaseProtoResult, SDKType


@dataclass(frozen=True)
class TextToSpeechResult(BaseProtoResult[None]):
    """A class representing the partially parsed result of a Web search request
    with XML format.
    """

    @override
    @classmethod
    def _from_proto(cls, *, proto: UtteranceSynthesisResponse, sdk: SDKType) -> Self:
        return cls()
