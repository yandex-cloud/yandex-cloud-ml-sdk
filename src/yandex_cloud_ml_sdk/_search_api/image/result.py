# pylint: disable=protected-access
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchResponse

from yandex_cloud_ml_sdk._search_api.types import XMLBaseSearchResult, XMLSearchDocument
from yandex_cloud_ml_sdk._search_api.utils import NestedDict, get_element_text_dict, get_subelement_text
from yandex_cloud_ml_sdk._types.result import SDKType
from yandex_cloud_ml_sdk._utils.coerce import coerce_optional_int
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import ImageSearchConfig

if TYPE_CHECKING:
    from .image import BaseImageSearch


@dataclass(frozen=True)
class ImageSearchDocument(XMLSearchDocument):
    width: int | None
    height: int | None
    format: str | None
    extra: NestedDict

    @override
    @classmethod
    def _from_xml(cls, *, data: ET.Element, sdk: SDKType) -> Self:
        properties = data.find('image-properties')

        width = coerce_optional_int(get_subelement_text(properties, 'original-width'))
        height = coerce_optional_int(get_subelement_text(properties, 'original-height'))
        format_ = get_subelement_text(properties, 'mime-type')

        return cls(
            url=get_subelement_text(data, 'url'),
            domain=get_subelement_text(data, 'domain'),
            width=width,
            height=height,
            format=format_,
            modtime=cls._parse_modtime(data),
            extra=get_element_text_dict(data)
        )


class BaseImageSearchResult(
    XMLBaseSearchResult[ImageSearchResponse, ImageSearchDocument, ImageSearchConfig],
):
    """A class representing the partially parsed result of a Image search request
    with XML format.
    """

    _document_type = ImageSearchDocument

    @property
    def _model(self) -> BaseImageSearch:
        # pylint: disable-next=protected-access
        return self._sdk.search_api.image._model_type(
            sdk=self._sdk,
            config=self._request_details.model_config,
            uri='<search_api>'
        )

    @override
    async def _next_page(self, *, timeout: float | None = None) -> Self:
        """Run a image search request with previous search parameters
        except page number being increment by one.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds;
            if not given, initial timeout value from original search request are being used.
        """
        # pylint: disable-next=protected-access
        return await self._model._run(
            query=self._request_details.query,
            page=self._request_details.page + 1,
            timeout=timeout or self._request_details.timeout,
            format='parsed',
        )


@doc_from(BaseImageSearchResult)
class AsyncImageSearchResult(BaseImageSearchResult):
    @doc_from(BaseImageSearchResult._next_page)
    async def next_page(self, *, timeout: float | None = None) -> Self:
        return await self._next_page(timeout=timeout)


@doc_from(BaseImageSearchResult)
class ImageSearchResult(BaseImageSearchResult):
    __next_page = run_sync(BaseImageSearchResult._next_page)

    @doc_from(BaseImageSearchResult._next_page)
    def next_page(self, *, timeout: float | None = None) -> Self:
        return self.__next_page(timeout=timeout)


ImageSearchResultTypeT = TypeVar('ImageSearchResultTypeT', bound=BaseImageSearchResult)
