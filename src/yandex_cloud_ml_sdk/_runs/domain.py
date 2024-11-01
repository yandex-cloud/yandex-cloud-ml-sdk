# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import Run as ProtoRun
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import (
    CreateRunRequest, GetLastRunByThreadRequest, GetRunRequest, ListRunsRequest, ListRunsResponse
)
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2_grpc import RunServiceStub

from yandex_cloud_ml_sdk._assistants.assistant import BaseAssistant
from yandex_cloud_ml_sdk._assistants.utils import get_completion_options, get_prompt_trunctation_options
from yandex_cloud_ml_sdk._threads.thread import BaseThread
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .run import AsyncRun, Run, RunTypeT


class BaseRuns(BaseDomain, Generic[RunTypeT]):
    _run_impl: type[RunTypeT]

    async def _create(
        self,
        assistant: str | BaseAssistant,
        thread: str | BaseThread,
        *,
        stream: bool,
        custom_temperature: UndefinedOr[float] = UNDEFINED,
        custom_max_tokens: UndefinedOr[int] = UNDEFINED,
        custom_max_prompt_tokens: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60,
    ) -> RunTypeT:
        assistant_id: str
        if isinstance(assistant, str):
            assistant_id = assistant
        elif isinstance(assistant, BaseAssistant):
            assistant_id = assistant.id
        else:
            raise TypeError('assistant parameter must be a str either Assistant instance')

        thread_id: str
        if isinstance(thread, str):
            thread_id = thread
        elif isinstance(thread, BaseThread):
            thread_id = thread.id
        else:
            raise TypeError('thread parameter must be a str either Thread instance')

        request = CreateRunRequest(
            assistant_id=assistant_id,
            thread_id=thread_id,
            custom_completion_options=get_completion_options(
                temperature=get_defined_value(custom_temperature, None),
                max_tokens=get_defined_value(custom_max_tokens, None),
            ),
            custom_prompt_truncation_options=get_prompt_trunctation_options(
                max_prompt_tokens=get_defined_value(custom_max_prompt_tokens, None),
            ),
            stream=stream,
        )

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoRun,
            )

        return self._run_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get(
        self,
        run_id: str,
        *,
        timeout: float = 60,
    ) -> RunTypeT:
        # TODO: we need a global per-sdk cache on ids to rule out
        # possibility we have two Runs with same ids but different fields
        request = GetRunRequest(run_id=run_id)

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoRun,
            )

        return self._run_impl._from_proto(proto=response, sdk=self._sdk)

    async def _get_last_by_thread(
        self,
        thread: str | BaseThread,
        *,
        timeout: float = 60
    ) -> RunTypeT:
        thread_id: str
        if isinstance(thread, str):
            thread_id = thread
        elif isinstance(thread, BaseThread):
            thread_id = thread.id
        else:
            raise TypeError('thread parameter must be a str either Thread instance')

        request = GetLastRunByThreadRequest(thread_id=thread_id)

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.GetLastByThread,
                request,
                timeout=timeout,
                expected_type=ProtoRun,
            )

        return self._run_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[RunTypeT]:
        page_token_ = ''
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            while True:
                request = ListRunsRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListRunsResponse,
                )
                for run_proto in response.runs:
                    yield self._run_impl._from_proto(proto=run_proto, sdk=self._sdk)

                if not response.runs:
                    return

                page_token_ = response.next_page_token


class AsyncRuns(BaseRuns[AsyncRun]):
    # NB: there is no public 'create'
    _run_impl = AsyncRun

    async def get(
        self,
        run_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncRun:
        return await self._get(
            run_id=run_id,
            timeout=timeout,
        )

    async def get_last_by_thread(
        self,
        thread: str | BaseThread,
        *,
        timeout: float = 60
    ) -> AsyncRun:
        return await self._get_last_by_thread(
            thread=thread,
            timeout=timeout,
        )

    async def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncRun]:
        async for run in self._list(
            page_size=page_size,
            timeout=timeout,
        ):
            yield run


class Runs(BaseRuns[Run]):
    _run_impl = Run

    # NB: there is no public 'create'
    __get = run_sync(BaseRuns._get)
    __get_last_by_thread = run_sync(BaseRuns._get_last_by_thread)
    __list = run_sync_generator(BaseRuns._list)

    def get(
        self,
        run_id: str,
        *,
        timeout: float = 60,
    ) -> Run:
        return self.__get(
            run_id=run_id,
            timeout=timeout,
        )

    def get_last_by_thread(
        self,
        thread: str | BaseThread,
        *,
        timeout: float = 60
    ) -> Run:
        return self.__get_last_by_thread(
            thread=thread,
            timeout=timeout,
        )

    def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[Run]:
        yield from self.__list(
            page_size=page_size,
            timeout=timeout,
        )
