# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Iterator

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Author, ContentPart
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Message as ProtoMessage
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import MessageContent, Text
from yandex.cloud.ai.assistants.v1.threads.message_service_pb2 import (
    CreateMessageRequest, GetMessageRequest, ListMessagesRequest
)
from yandex.cloud.ai.assistants.v1.threads.message_service_pb2_grpc import MessageServiceStub

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.message import MessageType, coerce_to_text_message_dict
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .message import Message


class BaseMessages(BaseDomain):
    """
    Base class for message operations (sync and async implementations).
    """
    _message_impl = Message

    async def _create(
        self,
        message: MessageType,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        """Create a new message.

        :param message: Message content to create
        :param thread_id: ID of the thread to add message to
        :param labels: Optional dictionary of message labels
        :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        message_dict = coerce_to_text_message_dict(message)
        content = message_dict['text']
        author: Author | None = None
        if role := message_dict.get('role'):
            role = role.upper()
            # XXX: right now id is not validating anyhow, but it is required field
            # We passing random staff there.
            author = Author(role=role, id=self._client._user_agent)

        request = CreateMessageRequest(
            thread_id=thread_id,
            content=MessageContent(
                content=[ContentPart(
                    text=Text(content=content)
                )]
            ),
            labels=get_defined_value(labels, {}),
            author=author,
        )

        async with self._client.get_service_stub(MessageServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoMessage,
            )

        return self._message_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get(
        self,
        *,
        thread_id: str,
        message_id: str,
        timeout: float = 60,
    ) -> Message:
        """
        Get a message by ID.

        :param thread_id: ID of the thread containing the message
        :param message_id: ID of the message to retrieve
        :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        # TODO: we need a global per-sdk cache on ids to rule out
        # possibility we have two Messages with same ids but different fields
        request = GetMessageRequest(thread_id=thread_id, message_id=message_id)

        async with self._client.get_service_stub(MessageServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoMessage,
            )

        return self._message_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        thread_id: str,
        timeout: float = 60
    ) -> AsyncIterator[Message]:
        """
        List messages in a thread.

        :param thread_id: ID of the thread to list messages from
        :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        request = ListMessagesRequest(thread_id=thread_id)

        async with self._client.get_service_stub(MessageServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.List,
                request,
                timeout=timeout,
                expected_type=ProtoMessage,
            ):
                yield self._message_impl._from_proto(proto=response, sdk=self._sdk)

@doc_from(BaseMessages)
class AsyncMessages(BaseMessages):
    @doc_from(BaseMessages._create)
    async def create(
        self,
        message: MessageType,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return await self._create(
            message=message,
            thread_id=thread_id,
            labels=labels,
            timeout=timeout
        )

    @doc_from(BaseMessages._get)
    async def get(
        self,
        *,
        thread_id: str,
        message_id: str,
        timeout: float = 60,
    ) -> Message:
        return await self._get(
            thread_id=thread_id,
            message_id=message_id,
            timeout=timeout
        )

    @doc_from(BaseMessages._list)
    async def list(
        self,
        *,
        thread_id: str,
        timeout: float = 60
    ) -> AsyncIterator[Message]:
        async for message in self._list(
            thread_id=thread_id,
            timeout=timeout
        ):
            yield message

@doc_from(BaseMessages)
class Messages(BaseMessages):

    __get = run_sync(BaseMessages._get)
    __create = run_sync(BaseMessages._create)
    __list = run_sync_generator(BaseMessages._list)

    @doc_from(BaseMessages._create)
    def create(
        self,
        message: MessageType,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return self.__create(
            message=message,
            thread_id=thread_id,
            labels=labels,
            timeout=timeout
        )

    @doc_from(BaseMessages._get)
    def get(
        self,
        *,
        thread_id: str,
        message_id: str,
        timeout: float = 60,
    ) -> Message:
        return self.__get(
            thread_id=thread_id,
            message_id=message_id,
            timeout=timeout
        )

    @doc_from(BaseMessages._list)
    def list(
        self,
        *,
        thread_id: str,
        timeout: float = 60
    ) -> Iterator[Message]:
        yield from self.__list(
            thread_id=thread_id,
            timeout=timeout
        )
