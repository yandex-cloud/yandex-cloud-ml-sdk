# pylint: disable=protected-access
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchByImageResponse
from yandex_ai_studio_sdk._search_api.types import BaseSearchResult, SearchDocument, SearchRequestDetails
from yandex_ai_studio_sdk._types.proto import ProtoMirrored
from yandex_ai_studio_sdk._types.result import SDKType
from yandex_ai_studio_sdk._utils.doc import doc_from
from yandex_ai_studio_sdk._utils.sync import run_sync

from .config import ByImageSearchConfig

if TYPE_CHECKING:
    from .by_image import BaseByImageSearch


@dataclass(frozen=True)
class ByImageSearchDocument(SearchDocument, ProtoMirrored[ImageSearchByImageResponse.ImageInfo]):
    #: Image URL.
    url: str
    #: Image format.
    format: str | None
    #: Image width.
    width: int
    #: Image height.
    height: int
    #: Text passage.
    passage: str
    #: Document host.
    host: str
    #: Document title.
    page_title: str
    #: Document URL.
    page_url: str

    @override
    @classmethod
    def _kwargs_from_message(cls, proto: ImageSearchByImageResponse.ImageInfo, sdk: SDKType) -> dict[str, Any]:
        result = super()._kwargs_from_message(proto=proto, sdk=sdk)
        if format_ := result.get('format'):
            result['format'] = format_.removeprefix('IMAGE_FORMAT_').lower()
        return result


@dataclass(frozen=True)
class BaseByImageSearchResult(
    BaseSearchResult[ImageSearchByImageResponse, ByImageSearchDocument, ByImageSearchConfig],
):
    """A class representing the result of a search by image request."""

    images: tuple[ByImageSearchDocument, ...]
    cbir_id: str

    @override
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ImageSearchByImageResponse,
        sdk: SDKType,
        ctx: SearchRequestDetails[ByImageSearchConfig],
    ) -> Self:
        return cls(
            _sdk=sdk,
            _request_details=ctx,
            images=tuple(
                ByImageSearchDocument._from_proto(proto=image_data, sdk=sdk)
                for image_data in proto.images
            ),
            page=ctx.page,
            cbir_id=proto.id,
        )

    @property
    def docs(self) -> tuple[ByImageSearchDocument, ...]:
        """Synonym for .images attribute"""
        return self.images

    @property
    def _model(self) -> BaseByImageSearch:
        # pylint: disable-next=protected-access
        return self._sdk.search_api.by_image._model_type(
            sdk=self._sdk,
            config=self._request_details.model_config,
            uri='<search_api>'
        )

    @override
    async def _next_page(self, *, timeout: float | None = None) -> Self:
        """Run a search by image request with previous search parameters
        except page number being increment by one.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds;
            if not given, initial timeout value from original search request are being used.
        """
        # pylint: disable-next=protected-access
        return await self._model._run_from_id(
            cbir_id=self.cbir_id,
            page=self._request_details.page + 1,
            timeout=timeout or self._request_details.timeout,
        )


@doc_from(BaseByImageSearchResult)
class AsyncByImageSearchResult(BaseByImageSearchResult):
    @doc_from(BaseByImageSearchResult._next_page)
    async def next_page(self, *, timeout: float | None = None) -> Self:
        return await self._next_page(timeout=timeout)


@doc_from(BaseByImageSearchResult)
class ByImageSearchResult(BaseByImageSearchResult):
    __next_page = run_sync(BaseByImageSearchResult._next_page)

    @doc_from(BaseByImageSearchResult._next_page)
    def next_page(self, *, timeout: float | None = None) -> Self:
        return self.__next_page(timeout=timeout)


ByImageSearchResultTypeT = TypeVar('ByImageSearchResultTypeT', bound=BaseByImageSearchResult)
