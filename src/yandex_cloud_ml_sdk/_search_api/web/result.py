# pylint: disable=protected-access
from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from typing_extensions import Self
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchResponse

from yandex_cloud_ml_sdk._search_api.types import XMLBaseSearchResult, XMLSearchDocument
from yandex_cloud_ml_sdk._search_api.utils import (
    NestedDict, get_element_text, get_element_text_dict, get_subelement_text
)
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT
from yandex_cloud_ml_sdk._types.result import SDKType
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import WebSearchConfig

if TYPE_CHECKING:
    from .web import BaseWebSearch


@dataclass(frozen=True)
class WebSearchDocument(XMLSearchDocument):
    url: str | None
    domain: str | None
    title: str | None
    modtime: datetime.datetime | None
    lang: str | None
    extra: NestedDict

    passages: tuple[str, ...]

    @classmethod
    def _from_xml(cls, *, data: ET.Element, sdk: SDKType) -> Self:
        passages: list[str] = []
        for passage in data.iter('passage'):
            if text := get_element_text(passage):
                passages.append(text)

        modtime: datetime.datetime | None = None
        if raw_modtime := get_subelement_text(data, 'modtime'):
            raw_modtime = raw_modtime.strip()
            try:
                modtime = datetime.datetime.strptime(raw_modtime, '%Y%m%dT%H%M%S')
            except ValueError:
                pass

        return cls(
            url=get_subelement_text(data, 'url'),
            domain=get_subelement_text(data, 'domain'),
            title=get_subelement_text(data, 'title'),
            modtime=modtime,
            lang=get_subelement_text(data.find('properties'), 'lang'),
            passages=tuple(passages),
            extra=get_element_text_dict(data)
        )


class BaseWebSearchResult(
    XMLBaseSearchResult[WebSearchResponse, WebSearchDocument, WebSearchConfig],
    Generic[OperationTypeT]
):
    """A class representing the partially parsed result of a Web search request
    with XML format.
    """

    _operation_type: ClassVar[type[OperationTypeT]]
    _document_type = WebSearchDocument

    @property
    def _model(self) -> BaseWebSearch:
        # pylint: disable-next=protected-access
        return self._sdk.search_api.web._model_type(
            sdk=self._sdk,
            config=self._request_details.model_config,
            uri='<search_api>'
        )

    async def _next_page(self, *, timeout: float | None = None) -> Self:
        """Run a web search request with previous search parameters
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

    async def _next_page_deferred(self, *, timeout: float | None = None) -> OperationTypeT:
        """Launch a deferred web search request with previous search parameters
        except page number being increment by one.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds;
            if not given, initial timeout value from original search request are being used.
        """
        # pylint: disable-next=protected-access
        return await self._model._run_deferred(
            query=self._request_details.query,
            page=self._request_details.page + 1,
            timeout=timeout or self._request_details.timeout,
            format='parsed',
        )


@doc_from(BaseWebSearchResult)
class AsyncWebSearchResult(BaseWebSearchResult[AsyncOperation['AsyncWebSearchResult']]):
    _operation_type = AsyncOperation['AsyncWebSearchResult']

    @doc_from(BaseWebSearchResult._next_page)
    async def next_page(self, *, timeout: float | None = None) -> Self:
        return await self._next_page(timeout=timeout)

    @doc_from(BaseWebSearchResult._next_page_deferred)
    async def next_page_deferred(self, *, timeout: float | None = None) -> AsyncOperation['AsyncWebSearchResult']:
        return await self._next_page_deferred(timeout=timeout)


@doc_from(BaseWebSearchResult)
class WebSearchResult(BaseWebSearchResult[Operation['WebSearchResult']]):
    _operation_type = Operation['WebSearchResult']

    __next_page = run_sync(BaseWebSearchResult._next_page)  # pylint: disable=protected-access
    __next_page_deferred = run_sync(BaseWebSearchResult._next_page_deferred)  # pylint: disable=protected-access

    @doc_from(BaseWebSearchResult._next_page)
    def next_page(self, *, timeout: float | None = None) -> Self:
        return self.__next_page(timeout=timeout)

    @doc_from(BaseWebSearchResult._next_page_deferred)
    def next_page_deferred(self, *, timeout: float | None = None) -> Operation[WebSearchResult]:
        return self.__next_page_deferred(timeout=timeout)


WebSearchResultTypeT = TypeVar('WebSearchResultTypeT', bound=BaseWebSearchResult)
