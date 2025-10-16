from __future__ import annotations

import datetime
import itertools
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar, overload

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchResponse

from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT
from yandex_cloud_ml_sdk._types.result import BaseProtoResult, SDKType
from yandex_cloud_ml_sdk._types.xml import XMLBased
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import WebSearchConfig

if TYPE_CHECKING:
    from .web import BaseWebSearch

MAX_RECURSION_DEPTH = 255
MAX_RECURSION_TEXT = '<recursive parsing max depth reached>'


@dataclass(frozen=True)
class RequestDetails:
    model_config: WebSearchConfig
    page: int
    query: str
    timeout: float


def get_element_text(element: ET.Element, depth: int = 0) -> str:
    if depth >= MAX_RECURSION_DEPTH:
        return MAX_RECURSION_TEXT

    parts = []
    if element.text:
        parts.append(element.text)

    for child in element:
        parts.append(
            get_element_text(child, depth + 1)
        )

    if element.tail:
        parts.append(element.tail)

    return ''.join(parts).strip()


def get_subelement_text(subroot: ET.Element | None, name: str) -> str | None:
    if not subroot:
        return None

    element = subroot.find(name)
    if element is None:
        return None

    return get_element_text(element)


@dataclass(frozen=True)
class WebSearchDocument(XMLBased):
    url: str | None
    domain: str | None
    title: str | None
    modtime: datetime.datetime | None
    lang: str | None

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
        )


@dataclass(frozen=True)
class WebSearchGroup(XMLBased, Sequence):
    documents: tuple[WebSearchDocument, ...]

    @classmethod
    def _from_xml(cls, *, data: ET.Element, sdk: SDKType) -> Self:
        return cls(
            documents=tuple(
                WebSearchDocument._from_xml(data=el, sdk=sdk)
                for el in data.iter('doc')
            )
        )

    def __len__(self):
        return len(self.documents)

    @overload
    def __getitem__(self, index: int, /) -> WebSearchDocument:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[WebSearchDocument, ...]:
        pass

    def __getitem__(self, index, /):
        return self.documents[index]


@dataclass(frozen=True)
class BaseWebSearchResult(BaseProtoResult[WebSearchResponse], Sequence, Generic[OperationTypeT]):
    _sdk: SDKType = field(repr=False)
    _request_details: RequestDetails = field(repr=False)
    xml: bytes = field(repr=False)
    _operation_type: ClassVar[type[OperationTypeT]]

    page: int
    groups: tuple[WebSearchGroup, ...]

    @override
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: WebSearchResponse,
        sdk: SDKType,
        request_details: RequestDetails | None = None
    ) -> Self:
        assert request_details

        decoded = proto.raw_data.decode('utf-8')
        tree_root = ET.fromstring(decoded)

        response_data = tree_root.find('response')
        if response_data:
            groups = tuple(
                WebSearchGroup._from_xml(data=el, sdk=sdk)
                for el in response_data.iter('group')
            )
        else:
            groups = ()

        return cls(
            _sdk=sdk,
            _request_details=request_details,
            groups=groups,
            page=request_details.page,
            xml=proto.raw_data
        )

    def __len__(self):
        return len(self.groups)

    @property
    def docs(self) -> tuple[WebSearchDocument, ...]:
        return tuple(itertools.chain.from_iterable(self.groups))

    @overload
    def __getitem__(self, index: int, /) -> WebSearchGroup:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[WebSearchGroup, ...]:
        pass

    def __getitem__(self, index, /):
        return self.groups[index]

    @property
    def _model(self) -> BaseWebSearch:
        # pylint: disable-next=protected-access
        return self._sdk.search_api.web._model_type(
            sdk=self._sdk,
            config=self._request_details.model_config,
            uri='<search_api>'
        )

    async def _next_page(self, *, timeout: float | None = None) -> Self:
        # pylint: disable-next=protected-access
        return await self._model._run(
            query=self._request_details.query,
            page=self._request_details.page + 1,
            timeout=timeout or self._request_details.timeout,
            format='parsed',
        )

    async def _next_page_deferred(self, *, timeout: float | None = None) -> OperationTypeT:
        # pylint: disable-next=protected-access
        return await self._model._run_deferred(
            query=self._request_details.query,
            page=self._request_details.page + 1,
            timeout=timeout or self._request_details.timeout,
            format='parsed',
        )


class AsyncWebSearchResult(BaseWebSearchResult[AsyncOperation['AsyncWebSearchResult']]):
    _operation_type = AsyncOperation['AsyncWebSearchResult']

    async def next_page(self, *, timeout: float | None = None) -> Self:
        return await self._next_page(timeout=timeout)

    async def next_page_deferred(self, *, timeout: float | None = None) -> AsyncOperation['AsyncWebSearchResult']:
        return await self._next_page_deferred(timeout=timeout)


class WebSearchResult(BaseWebSearchResult[Operation['WebSearchResult']]):
    _operation_type = Operation['WebSearchResult']

    __next_page = run_sync(BaseWebSearchResult._next_page)  # pylint: disable=protected-access
    __next_page_deferred = run_sync(BaseWebSearchResult._next_page_deferred)  # pylint: disable=protected-access

    def next_page(self, *, timeout: float | None = None) -> Self:
        return self.__next_page(timeout=timeout)

    def next_page_deferred(self, *, timeout: float | None = None) -> Operation[WebSearchResult]:
        return self.__next_page_deferred(timeout=timeout)


WebSearchResultTypeT = TypeVar('WebSearchResultTypeT', bound=BaseWebSearchResult)
