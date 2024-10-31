# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Iterator

from yandex.cloud.ai.assistants.v1.threads.message_pb2 import ContentPart
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import Message as ProtoMessage
from yandex.cloud.ai.assistants.v1.threads.message_pb2 import MessageContent, Text
from yandex.cloud.ai.assistants.v1.threads.message_service_pb2 import (
    CreateMessageRequest, GetMessageRequest, ListMessagesRequest
)
from yandex.cloud.ai.assistants.v1.threads.message_service_pb2_grpc import MessageServiceStub

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .message import Message


class BaseMessages(BaseDomain):
    _message_impl = Message

    async def _create(
        self,
        content: str,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        request = CreateMessageRequest(
            thread_id=thread_id,
            content=MessageContent(
                content=[ContentPart(
                    text=Text(content=content)
                )]
            ),
            labels=get_defined_value(labels, {}),
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
        request = ListMessagesRequest(thread_id=thread_id)

        async with self._client.get_service_stub(MessageServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.List,
                request,
                timeout=timeout,
                expected_type=ProtoMessage,
            ):
                yield self._message_impl._from_proto(proto=response, sdk=self._sdk)


class AsyncMessages(BaseMessages):
    async def create(
        self,
        content: str,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return await self._create(
            content=content,
            thread_id=thread_id,
            labels=labels,
            timeout=timeout
        )

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


class Messages(BaseMessages):
    __get = run_sync(BaseMessages._get)
    __create = run_sync(BaseMessages._create)
    __list = run_sync_generator(BaseMessages._list)

    def create(
        self,
        content: str,
        *,
        thread_id: str,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Message:
        return self.__create(
            content=content,
            thread_id=thread_id,
            labels=labels,
            timeout=timeout
        )

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
