# pylint: disable=arguments-renamed,no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from collections.abc import Mapping
from typing import Generic, Literal, TypeVar, overload

from typing_extensions import Self, TypeAlias, override
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, Format, GroupMode, Localization, SearchType, SortMode, SortOrder
)
from yandex_cloud_ml_sdk._search_api.types import RequestDetails
from yandex_cloud_ml_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelAsyncMixin, ModelSyncMixin, OperationTypeT
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, BaseOperation, Operation
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import TextToSpeechConfig
from .result import TextToSpeechResult

logger = get_logger(__name__)


class BaseTextToSpeech(
    ModelSyncMixin[TextToSpeechConfig, TextToSpeechResult],
):
    """Web search class which provides concrete methods for working with Web Search API
    and incapsulates search setting.
    """

    _config_type = TextToSpeechConfig
    _result_type = TextToSpeechResult

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To learn more about parameters and their formats and possible values,
        refer to
        `web search documentation <https://yandex.cloud/ru/docs/search-api/concepts/web-search#parameters>`_

        :param search_type: Search type.
        :param family_mode: Results filtering.
        :param fix_typo_mode: Search query typo correction setting
        :param localization: Search response notifications language.
            Affects the text in the ``found-docs-human`` tag and error messages
        :param sort_mode: Search results sorting mode rule
        :param sort_order: Search results sorting order
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

        return super().configure(
        )

    @override
    def __repr__(self) -> str:
        # Web Search doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    @override
    async def _run(
        self,
        query: str,
        *,
        timeout: float = 60,
    ):
        """Run a search query with given ``query`` and search settings of this web search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.web(search_type='BE')
        >>> search = search.configure(search_type='RU')

        :param query: Search query text.
        :param format: With default ``parsed`` value call returns a parsed Yandex Cloud ML SDK
            object; with other values method returns a raw bytes string.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Parsed search results object or bytes string depending on ``format`` parameter.

        """

        return self._result_type._from_proto(
            proto=None,
            sdk=self._sdk,
        )


@doc_from(BaseTextToSpeech)
class AsyncTextToSpeech(BaseTextToSpeech):
    @doc_from(BaseTextToSpeech._run)
    async def run(
        self,
        query: str,
        *,
        timeout: float = 60
    ):
        return await self._run(query=query, timeout=timeout)


@doc_from(BaseTextToSpeech)
class TextToSpeech(BaseTextToSpeech):
    __run = run_sync(BaseTextToSpeech._run)

    @doc_from(BaseTextToSpeech._run)
    def run(
        self,
        query: str,
        *,
        timeout: float = 60
    ):
        return self.__run(query=query, timeout=timeout)


TextToSpeechTypeT = TypeVar('TextToSpeechTypeT', bound=BaseTextToSpeech)
