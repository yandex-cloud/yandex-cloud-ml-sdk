from __future__ import annotations

import datetime
import itertools
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import cached_property
from typing import ClassVar, Generic, TypeVar, Union, overload

from typing_extensions import Self, TypeAlias, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSearchResponse
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchResponse

from yandex_cloud_ml_sdk._types.model import BaseModel, ConfigTypeT
from yandex_cloud_ml_sdk._types.result import BaseProtoResult, ProtoMessageTypeT_contra, SDKType
from yandex_cloud_ml_sdk._types.xml import XMLBased

from .utils import get_subelement_text

XMLSearchProtoMessage: TypeAlias = Union[WebSearchResponse, ImageSearchResponse]
XMLSearchProtoMessageTypeT_contra = TypeVar(
    'XMLSearchProtoMessageTypeT_contra',
    bound=XMLSearchProtoMessage,
    contravariant=True
)


class SearchDocument:
    pass


@dataclass(frozen=True)
class XMLSearchDocument(SearchDocument, XMLBased):
    url: str | None
    domain: str | None
    modtime: datetime.datetime | None

    @staticmethod
    def _parse_modtime(data: ET.Element) -> datetime.datetime | None:
        if raw_modtime := get_subelement_text(data, 'modtime'):
            raw_modtime = raw_modtime.strip()
            try:
                return datetime.datetime.strptime(raw_modtime, '%Y%m%dT%H%M%S')
            except ValueError:
                pass

        return None


SearchDocumentTypeT = TypeVar('SearchDocumentTypeT', bound=SearchDocument)
XMLSearchDocumentTypeT = TypeVar('XMLSearchDocumentTypeT', bound=XMLSearchDocument)


@dataclass(frozen=True)
class RequestDetails(Generic[ConfigTypeT]):
    """:meta private:

    Object to incapsulate search settings into search result
    to make possible .next_page methods"""

    model_config: ConfigTypeT
    page: int
    query: str
    timeout: float


@dataclass(frozen=True)
class SearchGroup(XMLBased, Sequence, Generic[XMLSearchDocumentTypeT]):
    documents: tuple[XMLSearchDocumentTypeT, ...]

    @classmethod
    def _from_xml(
        cls,
        *,
        data: ET.Element,
        sdk: SDKType,
        document_type: type[XMLSearchDocumentTypeT] | None = None,
    ) -> SearchGroup[XMLSearchDocumentTypeT]:
        assert document_type
        return cls(
            documents=tuple(
                document_type._from_xml(data=el, sdk=sdk)
                for el in data.iter('doc')
            )
        )

    def __len__(self):
        return len(self.documents)

    @overload
    def __getitem__(self, index: int, /) -> XMLSearchDocumentTypeT:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[XMLSearchDocumentTypeT, ...]:
        pass

    def __getitem__(self, index, /):
        return self.documents[index]


@dataclass(frozen=True)
class BaseSearchResult(
    Generic[ProtoMessageTypeT_contra, SearchDocumentTypeT, ConfigTypeT],
    BaseProtoResult[ProtoMessageTypeT_contra],
    Sequence[SearchDocumentTypeT],
    ABC
):
    _sdk: SDKType = field(repr=False)
    _request_details: RequestDetails[ConfigTypeT] = field(repr=False)

    #: Returned search page number.
    page: int

    @property
    @abstractmethod
    def docs(self) -> tuple[SearchDocumentTypeT, ...]:
        """Returns all documents within search response."""

    @property
    @abstractmethod
    def _model(self) -> BaseModel:
        pass

    @abstractmethod
    async def _next_page(self, *, timeout: float | None = None) -> Self:
        pass

    def __len__(self) -> int:
        """Returns the number of documents in search response."""
        return len(self.docs)

    @overload
    def __getitem__(self, index: int, /) -> SearchDocumentTypeT:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[SearchDocumentTypeT, ...]:
        pass

    def __getitem__(self, index, /):
        """getitem implementation for search response documents."""
        return self.docs[index]


@dataclass(frozen=True)
class XMLBaseSearchResult(
    BaseSearchResult[XMLSearchProtoMessageTypeT_contra, XMLSearchDocumentTypeT, ConfigTypeT]
):
    #: Non-parsed XML result of search request.
    xml: bytes = field(repr=False)
    #: Parsed values of <group> tags within the response.
    groups: tuple[SearchGroup[XMLSearchDocumentTypeT], ...]
    _document_type: ClassVar[type[XMLSearchDocumentTypeT]]

    @override
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: XMLSearchProtoMessageTypeT_contra,
        sdk: SDKType,
        request_details: RequestDetails[ConfigTypeT] | None = None
    ) -> Self:
        assert request_details

        decoded = proto.raw_data.decode('utf-8')
        tree_root = ET.fromstring(decoded)

        response_data = tree_root.find('response')
        if response_data is not None:
            groups = tuple(
                SearchGroup[XMLSearchDocumentTypeT]._from_xml(
                    data=el, sdk=sdk, document_type=cls._document_type,
                )
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

    @cached_property
    def docs(self) -> tuple[XMLSearchDocumentTypeT, ...]:
        """Returns all documents within search response."""
        return tuple(itertools.chain.from_iterable(self.groups))
