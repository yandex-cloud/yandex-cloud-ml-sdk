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
    """
    Source document found for user query.

    Might be used or not used in generative answer itself.
    """

    #: Url of the document
    url: str
    #: Title of the document
    title: str
    #: Has this source been used in generative answer or not
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
    #: Text of the search query
    text: str
    #: Request id
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
    #: Generative answer itself.
    #: Note that footnootes like ``[N]`` in the text refers to ``GenerativeSearchResult.sources[N]``
    #: source.
    text: str
    #: Message sender role; in case of the generative search, model always answers with the
    #: "assistant" role.
    role: str
    #: Fixed query string in case of query was fixed
    fixed_misspell_query: str | None
    #: Anwer was rejected by some reasons, probably because of the ethics constrictions
    is_answer_rejected: bool
    #: Model was unable to give good answer and returned bulleted list with some info.
    is_bullet_answer: bool
    #: List of documents found by user query; every element number matches with footnotes in the ``.text`` attribute.
    sources: tuple[SearchSource, ...]
    #: List of search queries sent to model
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
        """Alias to ``GenerativeSearchResult.text``.

        Only to add some compatibility with raw Search API answer which have "content" field
        in protobufs and REST answers unlike other parts of this SDK.
        """

        return self.text
