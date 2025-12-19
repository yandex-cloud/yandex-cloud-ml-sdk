# pylint: disable=arguments-renamed,no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from typing import Generic, TypeVar

from typing_extensions import Self, override
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchByImageRequest, ImageSearchByImageResponse
from yandex.cloud.searchapi.v2.img_search_service_pb2_grpc import ImageSearchServiceStub

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._search_api.enums import FamilyMode
from yandex_cloud_ml_sdk._search_api.types import SearchRequestDetails
from yandex_cloud_ml_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import ByImageSearchConfig
from .result import AsyncByImageSearchResult, ByImageSearchResult, ByImageSearchResultTypeT

logger = get_logger(__name__)


class BaseByImageSearch(
    Generic[ByImageSearchResultTypeT],
    ModelSyncMixin[ByImageSearchConfig, ByImageSearchResultTypeT],
):
    """ByImage search class which provides concrete methods for working with ByImage Search API
    and incapsulates search setting.
    """

    _config_type = ByImageSearchConfig
    _result_type: type[ByImageSearchResultTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] | None = UNDEFINED,
        site: UndefinedOr[str] | None = UNDEFINED,
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

        To learn more about parameters and their formats and possible values,
        refer to
        `search by image documentation <https://yandex.cloud/ru/docs/search-api/concepts/image-search#request-body-by-pic>`_

        :param family_mode: Results filtering.
        :param site: Restricts the search to the specific website.
        """

        return super().configure(
            family_mode=family_mode,
            site=site,
        )

    @override
    def __repr__(self) -> str:
        # Search by image doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    async def _run_impl(
        self,
        *,
        image_data: bytes | None = None,
        id_: str | None = None,
        url: str | None = None,
        page: int,
        timeout: float,
    ) -> ByImageSearchResultTypeT:
        assert sum(x is not None for x in (image_data, id_, url)) == 1
        query_dict = {
            'data': image_data,
            'id': id_,
            'url': url,
        }

        request = ImageSearchByImageRequest(
            folder_id=self._sdk._folder_id,
            page=page,
            family_mode=self._config.family_mode or 0,  # type: ignore[arg-type]
            site=self._config.site or '',
            **query_dict  # type: ignore[arg-type]
        )

        async with self._client.get_service_stub(ImageSearchServiceStub, timeout=timeout) as stub:
            response: ImageSearchByImageResponse = await self._client.call_service(
                stub.SearchByImage,
                request,
                timeout=timeout,
                expected_type=ImageSearchByImageResponse
            )

        return self._result_type._from_proto(
            proto=response,
            sdk=self._sdk,
            ctx=SearchRequestDetails(
                model_config=self._config,
                page=page,
                query='<not-needed>',
                timeout=timeout,
            )
        )

    @override
    async def _run(
        self,
        image_data: bytes,
        *,
        page: int = 0,
        timeout: float = 60,
    ) -> ByImageSearchResultTypeT:
        """Run a search query with given ``image_data`` bytes and search settings of this by_image search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.by_image(site="ya.ru")
        >>> search = search.configure(site="yandex.ru")

        :param image_data: The image data to use for the search.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Parsed search results object.

        """

        return await self._run_impl(image_data=image_data, page=page, timeout=timeout)

    async def _run_from_url(
        self,
        url: str,
        *,
        page: int = 0,
        timeout: float = 60,
    ) -> ByImageSearchResultTypeT:
        """Run a search query with given image located at ``url`` and search settings of this by_image search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.by_image(site="ya.ru")
        >>> search = search.configure(site="yandex.ru")

        :param url: The image url to use for the search.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Parsed search results object.

        """

        return await self._run_impl(url=url, page=page, timeout=timeout)

    async def _run_from_id(
        self,
        cbir_id: str,
        *,
        page: int = 0,
        timeout: float = 60,
    ) -> ByImageSearchResultTypeT:
        """Run a search query with given CBIR ID of the image and search settings of this by_image search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.by_image(site="ya.ru")
        >>> search = search.configure(site="yandex.ru")

        :param id: CBIR ID of the image to use for the search.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Parsed search results object.

        """

        return await self._run_impl(id_=cbir_id, page=page, timeout=timeout)


@doc_from(BaseByImageSearch)
class AsyncByImageSearch(
    BaseByImageSearch[AsyncByImageSearchResult]
):
    _result_type = AsyncByImageSearchResult

    @doc_from(BaseByImageSearch._run)
    async def run(
        self,
        image_data: bytes,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> AsyncByImageSearchResult:
        return await self._run(image_data=image_data, page=page, timeout=timeout)

    @doc_from(BaseByImageSearch._run_from_url)
    async def run_from_url(
        self,
        url: str,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> AsyncByImageSearchResult:
        return await self._run_from_url(url=url, page=page, timeout=timeout)

    @doc_from(BaseByImageSearch._run_from_id)
    async def run_from_id(
        self,
        cbir_id: str,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> AsyncByImageSearchResult:
        return await self._run_from_id(cbir_id=cbir_id, page=page, timeout=timeout)




@doc_from(BaseByImageSearch)
class ByImageSearch(BaseByImageSearch[ByImageSearchResult]):
    _result_type = ByImageSearchResult

    __run = run_sync(BaseByImageSearch._run)
    __run_from_url = run_sync(BaseByImageSearch._run_from_url)
    __run_from_id = run_sync(BaseByImageSearch._run_from_id)

    @doc_from(BaseByImageSearch._run)
    def run(
        self,
        image_data: bytes,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> ByImageSearchResult:
        return self.__run(image_data=image_data, page=page, timeout=timeout)

    @doc_from(BaseByImageSearch._run_from_url)
    def run_from_url(
        self,
        url: str,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> ByImageSearchResult:
        return self.__run_from_url(url=url, page=page, timeout=timeout)

    @doc_from(BaseByImageSearch._run_from_id)
    def run_from_id(
        self,
        cbir_id: str,
        *,
        page: int = 0,
        timeout: float = 60
    ) -> ByImageSearchResult:
        return self.__run_from_id(cbir_id=cbir_id, page=page, timeout=timeout)




ByImageSearchTypeT = TypeVar('ByImageSearchTypeT', bound=BaseByImageSearch)
