from __future__ import annotations

from collections.abc import Mapping

from typing_extensions import override

from yandex_cloud_ml_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder
)
from yandex_cloud_ml_sdk._types.enum import EnumWithUnknownInput, UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .config import TextToSpeechConfig
from .tts import AsyncTextToSpeech, TextToSpeech, TextToSpeechTypeT


class BaseTextToSpeechFunction(BaseModelFunction[TextToSpeechTypeT]):
    """Web search function for creating search object which provides
    methods for invoking web search.
    """

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
    ) -> TextToSpeechTypeT:
        """
        Creates web search object which provides methods for web search.

        To learn more about parameters and their formats and possible values,
        refer to
        `web search documentation <https://yandex.cloud/ru/docs/search-api/concepts/web-search#parameters>`_

        :param search_type: Search type.
        :param family_mode: Results filtering.
        :param fix_typo_mode: Search query typo correction setting
        :param localization: Search response notifications language.
            Affects the text in the ``found-docs-human`` tag and error messages
        :param sort_order: Search results sorting order
        :param sort_mode: Search results sorting mode rule
        :param group_mode: Result grouping method.
        :param groups_on_page: Maximum number of groups that can be returned per page.
        :param docs_in_group: Maximum number of documents that can be returned per group.
        :param max_passages: Maximum number of passages that can be used when generating
            a document.
        :param region: Search country or region ID that affects the document ranking rules.
        :param user_agent: String containing the User-Agent header.
            Use this parameter to have your search results optimized for a
            specific device and browser, including mobile search results.
        """
        tts = self._model_type(sdk=self._sdk, uri='<speechkit>')

        return tts.configure(
        )


@doc_from(BaseTextToSpeechFunction)
class TextToSpeechFunction(BaseTextToSpeechFunction[TextToSpeech]):
    _model_type = TextToSpeech


@doc_from(BaseTextToSpeechFunction)
class AsyncTextToSpeechFunction(BaseTextToSpeechFunction[AsyncTextToSpeech]):
    _model_type = AsyncTextToSpeech
