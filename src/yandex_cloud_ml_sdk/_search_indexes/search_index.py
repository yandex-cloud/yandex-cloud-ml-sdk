# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, TypeVar

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.searchindex.search_index_pb2 import SearchIndex as ProtoSearchIndex
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2 import (
    DeleteSearchIndexRequest, DeleteSearchIndexResponse, UpdateSearchIndexRequest
)
from yandex.cloud.ai.assistants.v1.searchindex.search_index_service_pb2_grpc import SearchIndexServiceStub

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .index_type import BaseSearchIndexType

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseSearchIndex(ExpirableResource):
    _proto_result_type = ProtoSearchIndex

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
                'name': name,
                'description': description,
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
    async def _write(
        self,
        content: str,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        # pylint: disable-next=protected-access
        return await self._sdk._messages._create(
            search_index_id=self.id,
            content=content,
            labels=labels,
            timeout=timeout
        )

    async def _read(
        self,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[Message]:
        # NB: in other methods it is solved via @safe decorator, but it is doesn't work
        # with iterators, so, temporary here will be small copypaste
        # Also I'm not sure enough if we need to put whole SearchIndex reading under a lock
        if self._deleted:
            action = 'read'
            klass = self.__class__.__name__
            raise ValueError(f"you can't perform an action '{action}' on {klass}='{self.id}' because it is deleted")

        # pylint: disable-next=protected-access
        async for message in self._sdk._messages._list(search_index_id=self.id, timeout=timeout):
            yield message


@dataclasses.dataclass(frozen=True)
class RichSearchIndex(BaseSearchIndex):
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


class AsyncSearchIndex(RichSearchIndex):
    update = RichSearchIndex._update
    delete = RichSearchIndex._delete
    write = RichSearchIndex._write
    read = RichSearchIndex._read
    __aiter__ = RichSearchIndex._read


class SearchIndex(RichSearchIndex):
    update = run_sync(RichSearchIndex._update)
    delete = run_sync(RichSearchIndex._delete)
    write = run_sync(RichSearchIndex._write)
    read = run_sync_generator(RichSearchIndex._read)
    __iter__ = run_sync_generator(RichSearchIndex._read)


SearchIndexTypeT = TypeVar('SearchIndexTypeT', bound=BaseSearchIndex)
