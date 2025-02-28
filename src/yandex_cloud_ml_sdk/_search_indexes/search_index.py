# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, TypeVar, cast

from typing_extensions import Self, TypeAlias
from yandex.cloud.ai.assistants.v1.searchindex.search_index_file_pb2 import SearchIndexFile as ProtoSearchIndexFile
from yandex.cloud.ai.assistants.v1.searchindex.search_index_file_service_pb2 import (
    BatchCreateSearchIndexFileRequest, BatchCreateSearchIndexFileResponse, GetSearchIndexFileRequest,
    ListSearchIndexFilesRequest, ListSearchIndexFilesResponse
)
from yandex.cloud.ai.assistants.v1.searchindex.search_index_file_service_pb2_grpc import SearchIndexFileServiceStub
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2 import (
    DeleteSearchIndexRequest, DeleteSearchIndexResponse, UpdateSearchIndexRequest
)
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2_grpc import SearchIndexServiceStub
from yandex.cloud.operation.operation_pb2 import Operation as ProtoOperation

from yandex_cloud_ml_sdk._files.file import BaseFile
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.operation import AsyncOperation, Operation, OperationTypeT, ReturnsOperationMixin
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._types.result import BaseResult
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .file import SearchIndexFile
from .index_type import BaseSearchIndexType

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


SearchIndexFileTuple: TypeAlias = tuple[SearchIndexFile, ...]


@dataclasses.dataclass(frozen=True)
class BaseSearchIndex(ExpirableResource, BaseResult, ReturnsOperationMixin[OperationTypeT]):
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoSearchIndex, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        # pylint: disable=protected-access
        kwargs['index_type'] = BaseSearchIndexType._from_upper_proto(proto=proto, sdk=sdk)
        return kwargs

    @safe_on_delete
    async def _update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        # pylint: disable=too-many-locals
        name_ = get_defined_value(name, '')
        description_ = get_defined_value(description, '')
        labels_ = get_defined_value(labels, {})
        expiration_config = ExpirationConfig.coerce(
            ttl_days=ttl_days,
            expiration_policy=expiration_policy
        )

        request = UpdateSearchIndexRequest(
            search_index_id=self.id,
            name=name_,
            description=description_,
            labels=labels_,
            expiration_config=expiration_config.to_proto(),
        )

        self._fill_update_mask(
            request.update_mask,
            {
                'description': description,
                'name': name,  # this line is moved to avoid "duplicate-code" check of pylint XD
                'labels': labels,
                'expiration_config.ttl_days': ttl_days,
                'expiration_config.expiration_policy': expiration_policy
            }
        )

        async with self._client.get_service_stub(SearchIndexServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Update,
                request,
                timeout=timeout,
                expected_type=ProtoSearchIndex,
            )
        self._update_from_proto(response)

        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        request = DeleteSearchIndexRequest(search_index_id=self.id)

        async with self._client.get_service_stub(SearchIndexServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteSearchIndexResponse,
            )
            object.__setattr__(self, '_deleted', True)

    @safe_on_delete
    async def _get_file(
        self,
        file_id: str,
        *,
        timeout: float = 60
    ) -> SearchIndexFile:
        request = GetSearchIndexFileRequest(
            file_id=file_id,
            search_index_id=self.id
        )

        async with self._client.get_service_stub(SearchIndexFileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoSearchIndexFile,
            )

        return SearchIndexFile._from_proto(proto=response, sdk=self._sdk)

    # pylint: disable=unused-argument
    async def _transform_add_files(self, proto: BatchCreateSearchIndexFileResponse, timeout: float) -> SearchIndexFileTuple:
        return tuple(
            SearchIndexFile._from_proto(proto=f, sdk=self._sdk)
            for f in proto.files
        )

    @safe_on_delete
    async def _add_files_deferred(
        self,
        files: ResourceType[BaseFile],
        *,
        timeout: float = 60,
    ) -> OperationTypeT:
        file_ids = coerce_resource_ids(files, BaseFile)
        request = BatchCreateSearchIndexFileRequest(
            file_ids=file_ids,
            search_index_id=self.id
        )

        async with self._client.get_service_stub(SearchIndexFileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.BatchCreate,
                request,
                timeout=timeout,
                expected_type=ProtoOperation
            )

        return self._operation_impl(
            id=response.id,
            sdk=self._sdk,
            proto_result_type=BatchCreateSearchIndexFileResponse,
            result_type=SearchIndexFileTuple,
            transformer=self._transform_add_files
        )

    async def _list_files(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[SearchIndexFile]:
        page_token_ = ''
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(SearchIndexFileServiceStub, timeout=timeout) as stub:
            while True:
                request = ListSearchIndexFilesRequest(
                    search_index_id=self.id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListSearchIndexFilesResponse,
                )
                for search_index_proto in response.files:
                    yield SearchIndexFile._from_proto(proto=search_index_proto, sdk=self._sdk)

                if not response.files:
                    return

                page_token_ = response.next_page_token


@dataclasses.dataclass(frozen=True)
class RichSearchIndex(BaseSearchIndex[OperationTypeT]):
    folder_id: str
    name: str | None
    description: str | None
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    expires_at: datetime
    labels: dict[str, str] | None
    index_type: BaseSearchIndexType


class AsyncSearchIndex(RichSearchIndex[AsyncOperation[SearchIndexFileTuple]]):
    _operation_impl = AsyncOperation[SearchIndexFileTuple]

    async def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return await self._update(
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(timeout=timeout)

    async def get_file(
        self,
        file_id: str,
        *,
        timeout: float = 60
    ) -> SearchIndexFile:
        return await self._get_file(
            file_id=file_id,
            timeout=timeout
        )

    async def list_files(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[SearchIndexFile]:
        async for file in self._list_files(
            page_size=page_size,
            timeout=timeout,
        ):
            yield file

    async def add_files_deferred(
        self,
        files: ResourceType[BaseFile],
        *,
        timeout: float = 60,
    ) -> AsyncOperation[SearchIndexFileTuple]:
        return await self._add_files_deferred(
            files=files,
            timeout=timeout
        )


# pylint: disable=protected-access
class SearchIndex(RichSearchIndex[Operation[SearchIndexFileTuple]]):
    _operation_impl = Operation[SearchIndexFileTuple]
    __update = run_sync(RichSearchIndex._update)
    __delete = run_sync(RichSearchIndex._delete)
    __get_file = run_sync(RichSearchIndex._get_file)
    __list_files = run_sync_generator(RichSearchIndex._list_files)
    __add_files_deferred = run_sync(RichSearchIndex._add_files_deferred)

    def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return self.__update(
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(timeout=timeout)

    def get_file(
        self,
        file_id: str,
        *,
        timeout: float = 60
    ) -> SearchIndexFile:
        return self.__get_file(
            file_id=file_id,
            timeout=timeout
        )

    def list_files(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[SearchIndexFile]:
        yield from self.__list_files(
            page_size=page_size,
            timeout=timeout,
        )

    def add_files_deferred(
        self,
        files: ResourceType[BaseFile],
        *,
        timeout: float = 60,
    ) -> Operation[SearchIndexFileTuple]:
        # mypy is going crazy as always, with run_sync over generic
        return cast(
            Operation[SearchIndexFileTuple],
            self.__add_files_deferred(files=files, timeout=timeout)
        )


SearchIndexTypeT = TypeVar('SearchIndexTypeT', bound=BaseSearchIndex)
