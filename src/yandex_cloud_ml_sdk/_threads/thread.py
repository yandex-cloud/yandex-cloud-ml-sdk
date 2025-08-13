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
from yandex_cloud_ml_sdk._types.message import MessageType
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator


@dataclasses.dataclass(frozen=True)
class BaseThread(ExpirableResource[ProtoThread]):
    """A class for a thread resource.

    It provides methods for working with messages that the thread contains (e.g. updating, deleting, writing to, and reading from).
    """

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
        """Update the thread's properties, including the name, the description, labels,
        ttl days, and the expiration policy of the thread.

        :param name: the new name of the thread.
        :param description: the new description for the thread.
        :param labels: a set of new labels for the thread.
        :param ttl_days: the updated time-to-live in days for the thread.
        :param expiration_policy: an updated expiration policy for the file.
        :param timeout: timeout for the operation in seconds.
            Defaults to 60 seconds.
        """
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
        """Delete the thread.

        This method deletes the thread and marks it as deleted.
        Raises an exception if the deletion fails.

        :param timeout: timeout for the operation.
            Defaults to 60 seconds.
        """
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
        message: MessageType,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        """Write a message to the thread.

        This method allows sending a message to the thread with optional labels.

        :param message: the message to be sent to the thread. Could be a string, a dictionary, or a result object.
            Read more about other possible message types in the `documentation <https://yandex.cloud/docs/foundation-models/sdk/#usage>`_.
        :param labels: optional labels for the message.
        :param timeout: timeout for the operation.
            Defaults to 60 seconds.
        """
        # pylint: disable-next=protected-access
        return await self._sdk._messages._create(
            thread_id=self.id,
            message=message,
            labels=labels,
            timeout=timeout
        )

    async def _read(
        self,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[Message]:
        """Read messages from the thread.

        This method allows iterating over messages in the thread.

        :param timeout: timeout for the operation.
            Defaults to 60 seconds.
        """
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
    #: the name of the thread
    name: str | None
    #: the description of the thread
    description: str | None
    #: the identifier of the user who created the thread
    created_by: str
    #: the timestamp when the thread was created
    created_at: datetime
    #: the identifier of the user who last updated the thread
    updated_by: str
    #: the timestamp when the thread was last updated
    updated_at: datetime
    #: the timestamp when the thread will expire
    expires_at: datetime
    #: additional labels associated with the thread
    labels: dict[str, str] | None

class AsyncThread(RichThread):

    @doc_from(BaseThread._update)
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

    @doc_from(BaseThread._delete)
    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(timeout=timeout)

    @doc_from(BaseThread._write)
    async def write(
        self,
        message: MessageType,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return await self._write(
            message=message,
            labels=labels,
            timeout=timeout
        )

    @doc_from(BaseThread._read)
    async def read(
        self,
        *,
        timeout: float = 60,
    ) -> AsyncIterator[Message]:
        async for message in self._read(timeout=timeout):
            yield message

    #: alias for the read method
    __aiter__ = read

class Thread(RichThread):
    __update = run_sync(RichThread._update)
    __delete = run_sync(RichThread._delete)
    __write = run_sync(RichThread._write)
    __read = run_sync_generator(RichThread._read)

    @doc_from(BaseThread._update)
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

    @doc_from(BaseThread._delete)
    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(timeout=timeout)

    @doc_from(BaseThread._write)
    def write(
        self,
        message: MessageType,
        *,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return self.__write(
            message=message,
            labels=labels,
            timeout=timeout
        )

    @doc_from(BaseThread._read)
    def read(
        self,
        *,
        timeout: float = 60,
    ) -> Iterator[Message]:
        yield from self.__read(timeout=timeout)

    __iter__ = read


ThreadTypeT = TypeVar('ThreadTypeT', bound=BaseThread)
