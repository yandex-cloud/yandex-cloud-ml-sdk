from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .text_to_speech.function import AsyncTextToSpeechFunction, BaseTextToSpeechFunction, TextToSpeechFunction


class BaseSpeechKitDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex SpeechKit services <https://yandex.cloud/docs/speechkit/>`_.
    """

    #: API for `text to speech <https://yandex.cloud/docs/speechkit/tts/>`_ service
    text_to_speech: BaseTextToSpeechFunction
    #: Synonym for `text_to_speech` function
    tts: BaseTextToSpeechFunction


@doc_from(BaseSpeechKitDomain)
class AsyncSpeechKitDomain(BaseSpeechKitDomain):
    text_to_speech: AsyncTextToSpeechFunction
    tts: AsyncTextToSpeechFunction


@doc_from(BaseSpeechKitDomain)
class SpeechKitDomain(BaseSpeechKitDomain):
    text_to_speech: TextToSpeechFunction
    tts: TextToSpeechFunction
