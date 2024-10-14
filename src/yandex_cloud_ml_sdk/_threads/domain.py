# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, TypeVar

from yandex.cloud.ai.assistants.v1.threads.thread_pb2 import Thread as ProtoThread
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2 import (
    CreateThreadRequest, GetThreadRequest, ListThreadsRequest, ListThreadsResponse
)
from yandex.cloud.ai.assistants.v1.threads.thread_service_pb2_grpc import ThreadServiceStub

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyTypeT
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, is_defined
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .thread import AsyncThread, BaseThread, Thread

ThreadTypeT = TypeVar('ThreadTypeT', bound=BaseThread)


class BaseThreads(BaseDomain, Generic[ThreadTypeT]):
    _thread_impl: type[ThreadTypeT]

    async def _create(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyTypeT] = UNDEFINED,
        timeout: float = 60,
    ) -> ThreadTypeT:
        if is_defined(ttl_days) != is_defined(expiration_policy):
            raise ValueError("ttl_days and expiration policy must be both defined either undefined")

        expiration_config = ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)

        request = CreateThreadRequest(
            folder_id=self._folder_id,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
            expiration_config=expiration_config.to_proto(),
        )

        async with self._client.get_service_stub(ThreadServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoThread,
            )

        return self._thread_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get(
        self,
        thread_id: str,
        *,
        timeout: float = 60,
    ) -> ThreadTypeT:
        # TODO: we need a global per-sdk cache on ids to rule out
        # possibility we have two Threads with same ids but different fields
        request = GetThreadRequest(thread_id=thread_id)

        async with self._client.get_service_stub(ThreadServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoThread,
            )

        return self._thread_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[ThreadTypeT]:
        page_token_ = get_defined_value(page_token, '')
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(ThreadServiceStub, timeout=timeout) as stub:
            while True:
                request = ListThreadsRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListThreadsResponse,
                )
                for thread_proto in response.threads:
                    yield self._thread_impl._from_proto(proto=thread_proto, sdk=self._sdk)

                if not response.threads:
                    return

                page_token_ = response.next_page_token


class AsyncThreads(BaseThreads[AsyncThread]):
    _thread_impl = AsyncThread

    get = BaseThreads._get
    create = BaseThreads._create
    list = BaseThreads._list


class Threads(BaseThreads[Thread]):
    _thread_impl = Thread

    get = run_sync(BaseThreads._get)
    create = run_sync(BaseThreads._create)
    list = run_sync_generator(BaseThreads._list)
