# pylint: disable=arguments-renamed,no-name-in-module,redefined-builtin,protected-access
from __future__ import annotations

from collections.abc import Mapping
from typing import Generic, Literal, TypeVar, overload

from typing_extensions import Self, TypeAlias, override
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation
from yandex.cloud.searchapi.v2.search_query_pb2 import SearchMetadata, SearchQuery
from yandex.cloud.searchapi.v2.search_service_pb2 import GroupSpec, SortSpec, WebSearchRequest, WebSearchResponse
from yandex.cloud.searchapi.v2.search_service_pb2_grpc import WebSearchAsyncServiceStub, WebSearchServiceStub

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

from .config import WebSearchConfig
from .result import AsyncWebSearchResult, WebSearchResult, WebSearchResultTypeT

logger = get_logger(__name__)


SearchFormat: TypeAlias = Literal['parsed', 'xml', 'html']
AnotherOperationTypeT = TypeVar('AnotherOperationTypeT', bound=BaseOperation)
ProtoResponseTypeT = TypeVar('ProtoResponseTypeT', ProtoOperation, WebSearchResponse)


class BaseWebSearch(
    Generic[OperationTypeT, AnotherOperationTypeT, WebSearchResultTypeT],
    ModelSyncMixin[WebSearchConfig, WebSearchResultTypeT],
    ModelAsyncMixin[WebSearchConfig, WebSearchResultTypeT, OperationTypeT],
):
    """Web search class which provides concrete methods for working with Web Search API
    and incapsulates search setting.
    """

    _config_type = WebSearchConfig
    _result_type: type[WebSearchResultTypeT]
    _operation_type: type[OperationTypeT]
    _operation_type_raw: type[AnotherOperationTypeT]

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        search_type: UndefinedOrEnumWithUnknownInput[SearchType] | None = UNDEFINED,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] | None = UNDEFINED,
        fix_typo_mode: UndefinedOrEnumWithUnknownInput[FixTypoMode] | None = UNDEFINED,
        localization: UndefinedOrEnumWithUnknownInput[Localization] | None = UNDEFINED,
        sort_order: UndefinedOrEnumWithUnknownInput[SortOrder] | None = UNDEFINED,
        sort_mode: UndefinedOrEnumWithUnknownInput[SortMode] | None = UNDEFINED,
        group_mode: UndefinedOrEnumWithUnknownInput[GroupMode] | None = UNDEFINED,
        groups_on_page: UndefinedOr[int] | None = UNDEFINED,
        docs_in_group: UndefinedOr[int] | None = UNDEFINED,
        max_passages: UndefinedOr[int] | None = UNDEFINED,
        region: UndefinedOr[str] | None = UNDEFINED,
        user_agent: UndefinedOr[str] | None = UNDEFINED,
        metadata: UndefinedOr[Mapping[str, str]] | None = UNDEFINED,
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
            search_type=search_type,
            family_mode=family_mode,
            fix_typo_mode=fix_typo_mode,
            localization=localization,
            sort_order=sort_order,
            sort_mode=sort_mode,
            group_mode=group_mode,
            groups_on_page=groups_on_page,
            docs_in_group=docs_in_group,
            max_passages=max_passages,
            region=region,
            user_agent=user_agent,
            metadata=metadata,
        )

    @override
    def __repr__(self) -> str:
        # Web Search doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    async def _run_impl(
        self,
        *,
        page: int,
        query: str,
        timeout: float,
        format: SearchFormat,
        stub_class: type[WebSearchServiceStub | WebSearchAsyncServiceStub],
        expected_type: type[ProtoResponseTypeT],
    ) -> ProtoResponseTypeT:
        c = self._config
        request = WebSearchRequest(
            query=SearchQuery(
                family_mode=c.family_mode,  # type: ignore[arg-type]
                fix_typo_mode=c.fix_typo_mode,  # type: ignore[arg-type]
                page=page,
                query_text=query,
                search_type=c.search_type,  # type: ignore[arg-type]
            ),
            folder_id=self._sdk._folder_id,
            group_spec=GroupSpec(
                docs_in_group=c.docs_in_group or 0,
                groups_on_page=c.groups_on_page or 0,
                group_mode=c.group_mode,  # type: ignore[arg-type]
            ),
            l10n=c.localization,  # type: ignore[arg-type]
            max_passages=c.max_passages or 0,
            metadata=SearchMetadata(fields=c.metadata) if c.metadata else None,
            region=c.region or '',
            response_format=Format._coerce(format),  # type: ignore[arg-type]
            sort_spec=SortSpec(
                sort_mode=c.sort_mode,  # type: ignore[arg-type]
                sort_order=c.sort_order  # type: ignore[arg-type]
            ),
            user_agent=c.user_agent or '',
        )

        async with self._client.get_service_stub(stub_class, timeout=timeout) as stub:
            response: ProtoResponseTypeT = await self._client.call_service(
                stub.Search,
                request,
                timeout=timeout,
                expected_type=expected_type
            )

        return response

    @overload
    async def _run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60,
    ) -> WebSearchResultTypeT:
        ...

    @overload
    async def _run(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
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
        request_format = 'xml' if format == 'parsed' else format
        response = await self._run_impl(
            query=query,
            page=page,
            format=request_format,
            stub_class=WebSearchServiceStub,
            expected_type=WebSearchResponse,
            timeout=timeout
        )

        if format != 'parsed':
            return response.raw_data

        return self._result_type._from_proto(
            proto=response,
            sdk=self._sdk,
            request_details=RequestDetails(
                model_config=self._config,
                page=page,
                query=query,
                timeout=timeout
            )
        )

    @overload
    async def _run_deferred(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60
    ) -> OperationTypeT:
        ...

    @overload
    async def _run_deferred(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
        page: int = 0,
        timeout: float = 60
    ) -> AnotherOperationTypeT:
        ...

    @override
    async def _run_deferred(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        """Run a deferred search query with given ``query`` and search settings of this
        web search object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.web(search_type='BE')
        >>> search = search.configure(search_type='RU')

        :param query: Search query text.
        :param format: With default ``parsed`` value call returns an operation
            with parsed Yandex Cloud ML SDK return;
            with other values method returns an operation with raw bytes string return.
        :param page: Requested page number.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
        :returns: Operation with parsed search results object or bytes string return depending on ``format`` parameter.

        """
        request_format = 'xml' if format == 'parsed' else format
        response = await self._run_impl(
            query=query,
            page=page,
            format=request_format,
            stub_class=WebSearchAsyncServiceStub,
            expected_type=ProtoOperation,
            timeout=timeout
        )

        if format == 'parsed':
            async def transformer(proto: WebSearchResponse, *_) -> WebSearchResultTypeT:
                return self._result_type._from_proto(
                    proto=proto,
                    sdk=self._sdk,
                    request_details=RequestDetails(
                        model_config=self._config,
                        page=page,
                        query=query,
                        timeout=timeout
                    )
                )

            return self._operation_type(
                sdk=self._sdk,
                id=response.id,
                result_type=self._result_type,
                proto_result_type=WebSearchResponse,
                initial_operation=response,
                transformer=transformer
            )

        async def transformer_raw(proto: WebSearchResponse, *_) -> bytes:
            return proto.raw_data

        return self._operation_type_raw(
            sdk=self._sdk,
            id=response.id,
            result_type=bytes,
            proto_result_type=WebSearchResponse,
            initial_operation=response,
            transformer=transformer_raw
        )


@doc_from(BaseWebSearch)
class AsyncWebSearch(
    BaseWebSearch[AsyncOperation[AsyncWebSearchResult], AsyncOperation[bytes], AsyncWebSearchResult]
):
    _operation_type = AsyncOperation[AsyncWebSearchResult]
    _operation_type_raw = AsyncOperation[bytes]
    _result_type = AsyncWebSearchResult

    @overload
    async def run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60
    ) -> AsyncWebSearchResult:
        ...

    @overload
    async def run(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
        page: int = 0,
        timeout: float = 60
    ) -> bytes:
        ...

    @doc_from(BaseWebSearch._run)
    async def run(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return await self._run(query=query, format=format, page=page, timeout=timeout)

    @overload
    async def run_deferred(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60
    ) -> AsyncOperation[AsyncWebSearchResult]:
        ...

    @overload
    async def run_deferred(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
        page: int = 0,
        timeout: float = 60
    ) -> AsyncOperation[bytes]:
        ...

    @doc_from(BaseWebSearch._run_deferred)
    async def run_deferred(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return await self._run_deferred(query=query, format=format, page=page, timeout=timeout)


@doc_from(BaseWebSearch)
class WebSearch(BaseWebSearch[Operation[WebSearchResult], Operation[bytes], WebSearchResult]):
    _operation_type = Operation[WebSearchResult]
    _operation_type_raw = Operation[bytes]
    _result_type = WebSearchResult

    __run = run_sync(BaseWebSearch._run)
    __run_deferred = run_sync(BaseWebSearch._run_deferred)

    @overload
    def run(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60
    ) -> WebSearchResult:
        ...

    @overload
    def run(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
        page: int = 0,
        timeout: float = 60
    ) -> bytes:
        ...

    @doc_from(BaseWebSearch._run)
    def run(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return self.__run(query=query, format=format, page=page, timeout=timeout)

    @overload
    def run_deferred(
        self,
        query: str,
        *,
        format: Literal['parsed'] = 'parsed',
        page: int = 0,
        timeout: float = 60
    ) -> Operation[WebSearchResult]:
        ...

    @overload
    def run_deferred(
        self,
        query: str,
        *,
        format: Literal['xml', 'html'],
        page: int = 0,
        timeout: float = 60
    ) -> Operation[bytes]:
        ...

    @doc_from(BaseWebSearch._run_deferred)
    def run_deferred(
        self,
        query: str,
        *,
        format: SearchFormat = 'parsed',
        page: int = 0,
        timeout: float = 60
    ):
        return self.__run_deferred(query=query, format=format, page=page, timeout=timeout)


WebSearchTypeT = TypeVar('WebSearchTypeT', bound=BaseWebSearch)
