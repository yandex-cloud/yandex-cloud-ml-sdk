# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import AsyncIterator, Iterator, TypeVar

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.threads.thread_pb2 import Thread as ProtoThread
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2 import (
    DeleteThreadRequest, DeleteThreadResponse, UpdateThreadRequest
)
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2_grpc import ThreadServiceStub

from yandex_cloud_ml_sdk._messages.message import Message
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator


@dataclasses.dataclass(frozen=True)
class BaseThread(ExpirableResource):
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

        request = UpdateThreadRequest(
            thread_id=self.id,
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

        async with self._client.get_service_stub(ThreadServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Update,
                request,
                timeout=timeout,
                expected_type=ProtoThread,
            )
        self._update_from_proto(response)

        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        request = DeleteThreadRequest(thread_id=self.id)

        async with self._client.get_service_stub(ThreadServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteThreadResponse,
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
            thread_id=self.id,
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
        # Also I'm not sure enough if we need to put whole thread reading under a lock
        if self._deleted:
            action = 'read'
            klass = self.__class__.__name__
            raise ValueError(f"you can't perform an action '{action}' on {klass}='{self.id}' because it is deleted")

        # pylint: disable-next=protected-access
        async for message in self._sdk._messages._list(thread_id=self.id, timeout=timeout):
            yield message


@dataclasses.dataclass(frozen=True)
class RichThread(BaseThread):
    name: str | None
    description: str | None
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    expires_at: datetime
    labels: dict[str, str] | None


class AsyncThread(RichThread):
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
            timeout=timeout,
        )

    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(timeout=timeout)

    async def write(
        self,
        content: str,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return await self._write(
            content=content,
            labels=labels,
            timeout=timeout
        )

    async def read(
        self,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[Message]:
        async for message in self._read(timeout=timeout):
            yield message

    __aiter__ = read


class Thread(RichThread):
    __update = run_sync(RichThread._update)
    __delete = run_sync(RichThread._delete)
    __write = run_sync(RichThread._write)
    __read = run_sync_generator(RichThread._read)

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
            timeout=timeout,
        )

    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(timeout=timeout)

    def write(
        self,
        content: str,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return self.__write(
            content=content,
            labels=labels,
            timeout=timeout
        )

    def read(
        self,
        *,
        timeout: float = 60,
    ) -> Iterator[Message]:
        yield from self.__read(timeout=timeout)

    __iter__ = read


ThreadTypeT = TypeVar('ThreadTypeT', bound=BaseThread)
