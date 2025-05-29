from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self, override
# pylint: disable-next=no-name-in-module
from yandex.cloud.searchapi.v2.gen_search_service_pb2 import GenSearchResponse, Role

from yandex_cloud_ml_sdk._types.message import TextMessage
from yandex_cloud_ml_sdk._types.proto import ProtoBased
from yandex_cloud_ml_sdk._types.result import BaseResult, SDKType


@dataclass(frozen=True)
class SearchSource(ProtoBased[GenSearchResponse.Source]):
    url: str
    title: str
    used: bool

    @override
    @classmethod
    def _from_proto(cls, *, proto: GenSearchResponse.Source, sdk: SDKType) -> Self:
        return cls(
            url=proto.url,
            title=proto.title,
            used=bool(proto.used)
        )


@dataclass(frozen=True)
class SearchQuery(ProtoBased[GenSearchResponse.SearchQuery]):
    text: str
    req_id: str

    @override
    @classmethod
    def _from_proto(cls, *, proto: GenSearchResponse.SearchQuery, sdk: SDKType) -> Self:
        return cls(
            text=proto.text,
            req_id=proto.req_id
        )


@dataclass(frozen=True)
class GenerativeSearchResult(BaseResult[GenSearchResponse], TextMessage):
    text: str
    role: str
    fixed_misspell_query: str | None
    is_answer_rejected: bool
    is_bullet_answer: bool
    sources: tuple[SearchSource, ...]
    search_queries: tuple[SearchQuery, ...]

    @override
    @classmethod
    def _from_proto(cls, *, proto: GenSearchResponse, sdk: SDKType) -> Self:
        role = Role.Name(proto.message.role).removeprefix('ROLE_').lower()
        sources = tuple(SearchSource._from_proto(proto=source, sdk=sdk) for source in proto.sources)
        search_queries = tuple(SearchQuery._from_proto(proto=source, sdk=sdk) for source in proto.search_queries)

        return cls(
            text=proto.message.content,
            role=role,
            fixed_misspell_query=proto.fixed_misspell_query,
            is_answer_rejected=proto.is_answer_rejected,
            is_bullet_answer=proto.is_bullet_answer,
            sources=sources,
            search_queries=search_queries,
        )

    @property
    def content(self) -> str:
        return self.text
