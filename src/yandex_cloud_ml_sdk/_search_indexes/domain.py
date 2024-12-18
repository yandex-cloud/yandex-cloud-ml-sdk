# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator

from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2 import (
    CreateSearchIndexRequest, GetSearchIndexRequest, ListSearchIndicesRequest, ListSearchIndicesResponse
)
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2_grpc import SearchIndexServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._files.file import BaseFile
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .index_type import BaseSearchIndexType
from .search_index import AsyncSearchIndex, SearchIndex, SearchIndexTypeT


class BaseSearchIndexes(BaseDomain, Generic[SearchIndexTypeT, OperationTypeT]):
    _impl: type[SearchIndexTypeT]
    _operation_type: type[OperationTypeT]

    # pylint: disable=too-many-locals
    async def _create_deferred(
        self,
        files: ResourceType[BaseFile],
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

        file_ids = coerce_resource_ids(files, BaseFile)

        expiration_config = ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)

        kwargs = {}
        if is_defined(index_type):
            if not isinstance(index_type, BaseSearchIndexType):
                raise TypeError('index type must be instance of BaseSearchIndexType')
            kwargs[index_type._proto_field_name] = index_type._to_proto()

        request = CreateSearchIndexRequest(
            folder_id=self._folder_id,
            file_ids=file_ids,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            expiration_config=expiration_config.to_proto(),
            **kwargs,  # type: ignore[arg-type]
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
            result_type=self._impl,
            proto_result_type=ProtoSearchIndex,
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
        timeout: float = 60
    ) -> AsyncIterator[SearchIndexTypeT]:
        page_token_ = ''
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

    async def create_deferred(
        self,
        files: ResourceType[BaseFile],
        *,
        index_type: UndefinedOr[BaseSearchIndexType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncOperation[AsyncSearchIndex]:
        return await self._create_deferred(
            files=files,
            index_type=index_type,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    async def get(
        self,
        search_index_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncSearchIndex:
        return await self._get(
            search_index_id=search_index_id,
            timeout=timeout,
        )

    async def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncSearchIndex]:
        async for search_index in self._list(
            page_size=page_size,
            timeout=timeout,
        ):
            yield search_index


class SearchIndexes(BaseSearchIndexes[SearchIndex, Operation[SearchIndex]]):
    _impl = SearchIndex
    _operation_type = Operation

    __get = run_sync(BaseSearchIndexes._get)
    __create_deferred = run_sync(BaseSearchIndexes._create_deferred)
    __list = run_sync_generator(BaseSearchIndexes._list)

    def create_deferred(
        self,
        files: ResourceType[BaseFile],
        *,
        index_type: UndefinedOr[BaseSearchIndexType] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Operation[SearchIndex]:
        return self.__create_deferred(
            files=files,
            index_type=index_type,
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    def get(
        self,
        search_index_id: str,
        *,
        timeout: float = 60,
    ) -> SearchIndex:
        return self.__get(
            search_index_id=search_index_id,
            timeout=timeout,
        )

    def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[SearchIndex]:
        yield from self.__list(
            page_size=page_size,
            timeout=timeout,
        )
