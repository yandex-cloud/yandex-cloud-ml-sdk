# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import AsyncIterator

from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.threads.thread_pb2 import Thread as ProtoThread
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2 import (
    DeleteThreadRequest, DeleteThreadResponse, UpdateThreadRequest
)
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2_grpc import ThreadServiceStub

from yandex_cloud_ml_sdk._messages.message import Message
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import BaseDeleteableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator


@dataclasses.dataclass(frozen=True)
class BaseThread(BaseDeleteableResource):
    @safe_on_delete
    async def _update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        name_ = get_defined_value(name, '')
        description_ = get_defined_value(description, '')
        labels_ = get_defined_value(labels, {})

        request = UpdateThreadRequest(
            thread_id=self.id,
            name=name_,
            description=description_,
            labels=labels_,
        )

        for key, value in (
            ('name', name_),
            ('description', description_),
            ('labels', labels_)
        ):
            if value is not None:
                request.update_mask.paths.append(key)

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
        # pylint: disable-next=protected-access
        async for message in self._sdk._messages._list(thread_id=self.id, timeout=timeout):
            yield message


@dataclasses.dataclass(frozen=True)
class RichThread(BaseThread):
    name: str | None
    description: str | None
    mime_type: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    expires_at: datetime
    labels: dict[str, str] | None


class AsyncThread(RichThread):
    update = RichThread._update
    delete = RichThread._delete
    write = RichThread._write
    read = RichThread._read
    __aiter__ = RichThread._read


class Thread(RichThread):
    update = run_sync(RichThread._update)
    delete = run_sync(RichThread._delete)
    write = run_sync(RichThread._write)
    read = run_sync_generator(RichThread._read)
    __iter__ = run_sync_generator(RichThread._read)
