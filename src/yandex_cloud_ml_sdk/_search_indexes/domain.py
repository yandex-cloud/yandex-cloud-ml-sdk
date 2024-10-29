# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic

from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import TextSearchIndex, VectorSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2 import (
    CreateSearchIndexRequest, GetSearchIndexRequest, ListSearchIndicesRequest, ListSearchIndicesResponse
)
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2_grpc import SearchIndexServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._files.utils import FileType, coerce_file_ids
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .index_type import BaseSearchIndexType, TextSearchIndexType, VectorSearchIndexType
from .search_index import AsyncSearchIndex, SearchIndex, SearchIndexTypeT


class BaseSearchIndexes(BaseDomain, Generic[SearchIndexTypeT, OperationTypeT]):
    _impl: type[SearchIndexTypeT]
    _operation_type: type[OperationTypeT]

    async def _create_deferred(
        self,
        files: FileType,
        *,
        index_type: UndefinedOr[BaseSearchIndexType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> OperationTypeT:
        if is_defined(ttl_days) != is_defined(expiration_policy):
            raise ValueError("ttl_days and expiration policy must be both defined either undefined")

        file_ids = coerce_file_ids(files)

        expiration_config = ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)

        vector_search_index: VectorSearchIndex | None = None
        text_search_index: TextSearchIndex | None = None
        if isinstance(index_type, VectorSearchIndexType):
            vector_search_index = index_type._to_proto()
        elif isinstance(index_type, TextSearchIndexType):
            text_search_index = index_type._to_proto()
        elif is_defined(index_type):
            raise TypeError('index type must be instance of SearchIndexType')

        request = CreateSearchIndexRequest(
            folder_id=self._folder_id,
            file_ids=file_ids,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            expiration_config=expiration_config.to_proto(),
            vector_search_index=vector_search_index,
            text_search_index=text_search_index,
        )

        async with self._client.get_service_stub(SearchIndexServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoOperation,
            )

        return self._operation_type(
            id=response.id,
            sdk=self._sdk,
            result_type=self._impl
        )

    async def _get(
        self,
        search_index_id: str,
        *,
        timeout: float = 60,
    ) -> SearchIndexTypeT:
        # TODO: we need a global per-sdk cache on ids to rule out
        # possibility we have two SearchIndexs with same ids but different fields
        request = GetSearchIndexRequest(search_index_id=search_index_id)

        async with self._client.get_service_stub(SearchIndexServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoSearchIndex,
            )

        return self._impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[SearchIndexTypeT]:
        page_token_ = get_defined_value(page_token, '')
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(SearchIndexServiceStub, timeout=timeout) as stub:
            while True:
                request = ListSearchIndicesRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListSearchIndicesResponse,
                )
                for search_index_proto in response.indices:
                    yield self._impl._from_proto(proto=search_index_proto, sdk=self._sdk)

                if not response.indices:
                    return

                page_token_ = response.next_page_token


class AsyncSearchIndexes(BaseSearchIndexes[AsyncSearchIndex, AsyncOperation[AsyncSearchIndex]]):
    _impl = AsyncSearchIndex
    _operation_type = AsyncOperation

    get = BaseSearchIndexes._get
    create_deferred = BaseSearchIndexes._create_deferred
    list = BaseSearchIndexes._list


class SearchIndexes(BaseSearchIndexes[SearchIndex, Operation[AsyncSearchIndex]]):
    _impl = SearchIndex
    _operation_type = Operation

    get = run_sync(BaseSearchIndexes._get)
    create_deferred = run_sync(BaseSearchIndexes._create_deferred)
    list = run_sync_generator(BaseSearchIndexes._list)
