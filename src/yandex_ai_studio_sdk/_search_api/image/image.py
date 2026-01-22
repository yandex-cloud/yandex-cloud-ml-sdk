# pylint: disable=arguments-renamed,no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from typing import Generic, Literal, TypeVar, overload

from typing_extensions import Self, TypeAlias, override
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchRequest, ImageSearchResponse, ImageSpec
from yandex.cloud.searchapi.v2.img_search_service_pb2_grpc import ImageSearchServiceStub
from yandex.cloud.searchapi.v2.search_query_pb2 import SearchQuery

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, ImageColor, ImageFormat, ImageOrientation, ImageSize, SearchType
)
from yandex_ai_studio_sdk._search_api.types import SearchRequestDetails
from yandex_ai_studio_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._types.model import ModelSyncMixin
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import ImageSearchConfig
from .result import AsyncImageSearchResult, ImageSearchResult, ImageSearchResultTypeT

logger = get_logger(__name__)


SearchFormat: TypeAlias = Literal['parsed', 'xml']


class BaseImageSearch(
    Generic[ImageSearchResultTypeT],
    ModelSyncMixin[ImageSearchConfig, ImageSearchResultTypeT],
):
    """Image search class which provides concrete methods for working with Image Search API
    and incapsulates search setting.
    """

    _config_type = ImageSearchConfig
    _result_type: type[ImageSearchResultTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        search_type: UndefinedOrEnumWithUnknownInput[SearchType] = UNDEFINED,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] | None = UNDEFINED,
        fix_typo_mode: UndefinedOrEnumWithUnknownInput[FixTypoMode] | None = UNDEFINED,
        format: UndefinedOrEnumWithUnknownInput[ImageFormat] | None = UNDEFINED,
        size: UndefinedOrEnumWithUnknownInput[ImageSize] | None = UNDEFINED,
        orientation: UndefinedOrEnumWithUnknownInput[ImageOrientation] | None = UNDEFINED,
        color: UndefinedOrEnumWithUnknownInput[ImageColor] | None = UNDEFINED,
        site: UndefinedOr[str] | None = UNDEFINED,
        docs_on_page: UndefinedOr[int] | None = UNDEFINED,
        user_agent: UndefinedOr[str] | None = UNDEFINED,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To learn more about parameters and their formats and possible values,
        refer to
        `image search documentation <https://yandex.cloud/ru/docs/search-api/concepts/image-search#parameters>`_

        :param search_type: Search type.
        :param family_mode: Results filtering.
        :param fix_typo_mode: Search query typo correction setting
        :param format: Searching for images in a particular format.
        :param size: Searching for images of a particular size.
        :param orientation: Searching for images with a particular orientation.
        :param color: Searching for images containing a particular color.
        :param site: Number of results per search result page.
        :param docs_on_page: Number of results per search result page.
        :param user_agent: String containing the User-Agent header.
            Use this parameter to have your search results optimized for a
            specific device and browser, including mobile search results.
        """

        return super().configure(
            search_type=search_type,
            family_mode=family_mode,
            fix_typo_mode=fix_typo_mode,
            format=format,
            size=size,
            orientation=orientation,
            color=color,
            site=site,
            docs_on_page=docs_on_page,
            user_agent=user_agent,
        )

    @override
    def __repr__(self) -> str:
        # Image Search doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    @overload
    async def _run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60,
    ) -> ImageSearchResultTypeT:
        ...

    @overload
    async def _run(
        self,
        query: str,
        *,
        format: Literal['xml'],
        page: int = 0,
        timeout: float = 60,
    ) -> bytes:
        ...

    @override
    async def _run(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60,
    ):
        """Run a search query with given ``query`` and search settings of this image search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.image(search_type='BE')
        >>> search = search.configure(search_type='RU')

        :param query: Search query text.
        :param format: With default ``parsed`` value call returns a parsed Yandex AI Studio SDK
            object; with other values method returns a raw bytes string.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Parsed search results object or bytes string depending on ``format`` parameter.

        """
        c = self._config
        request = ImageSearchRequest(
            docs_on_page=c.docs_on_page or 0,
            folder_id=self._sdk._folder_id,
            image_spec=ImageSpec(
                color=c.color or 0,  # type: ignore[arg-type]
                format=c.format or 0,  # type: ignore[arg-type]
                orientation=c.orientation or 0,  # type: ignore[arg-type]
                size=c.size or 0,  # type: ignore[arg-type]
            ),
            query=SearchQuery(
                family_mode=c.family_mode or 0,  # type: ignore[arg-type]
                fix_typo_mode=c.fix_typo_mode or 0,  # type: ignore[arg-type]
                page=page,
                query_text=query,
                search_type=c.search_type or 0,  # type: ignore[arg-type]
            ),
            site=c.site or '',
            user_agent=c.user_agent or '',
        )

        async with self._client.get_service_stub(ImageSearchServiceStub, timeout=timeout) as stub:
            response: ImageSearchResponse = await self._client.call_service(
                stub.Search,
                request,
                timeout=timeout,
                expected_type=ImageSearchResponse
            )

        if format != 'parsed':
            return response.raw_data

        return self._result_type._from_proto(
            proto=response,
            sdk=self._sdk,
            ctx=SearchRequestDetails(
                model_config=self._config,
                page=page,
                query=query,
                timeout=timeout
            )
        )


@doc_from(BaseImageSearch)
class AsyncImageSearch(
    BaseImageSearch[AsyncImageSearchResult]
):
    _result_type = AsyncImageSearchResult

    @overload
    async def run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60,
    ) -> AsyncImageSearchResult:
        ...

    @overload
    async def run(
        self,
        query: str,
        *,
        format: Literal['xml'],
        page: int = 0,
        timeout: float = 60,
    ) -> bytes:
        ...

    @doc_from(BaseImageSearch._run)
    async def run(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return await self._run(query=query, format=format, page=page, timeout=timeout)


@doc_from(BaseImageSearch)
class ImageSearch(BaseImageSearch[ImageSearchResult]):
    _result_type = ImageSearchResult

    __run = run_sync(BaseImageSearch._run)

    @overload
    def run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60,
    ) -> ImageSearchResult:
        ...

    @overload
    def run(
        self,
        query: str,
        *,
        format: Literal['xml'],
        page: int = 0,
        timeout: float = 60,
    ) -> bytes:
        ...

    @doc_from(BaseImageSearch._run)
    def run(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return self.__run(query=query, format=format, page=page, timeout=timeout)


ImageSearchTypeT = TypeVar('ImageSearchTypeT', bound=BaseImageSearch)
