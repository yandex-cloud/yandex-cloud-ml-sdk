# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, TypeVar

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import Run as ProtoRun
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import (
    CreateRunRequest, GetRunRequest, ListRunsRequest, ListRunsResponse
)
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2_grpc import RunServiceStub

from yandex_cloud_ml_sdk._assistants.domain import Assistant, AssistantTypeT, AsyncAssistant, BaseAssistant
from yandex_cloud_ml_sdk._assistants.utils import get_completion_options, get_prompt_trunctation_options
from yandex_cloud_ml_sdk._threads.domain import AsyncThread, BaseThread, Thread, ThreadTypeT
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .run import AsyncRun, BaseRun, Run

RunTypeT = TypeVar('RunTypeT', bound=BaseRun)


class BaseRuns(BaseDomain, Generic[RunTypeT, AssistantTypeT, ThreadTypeT]):
    _run_impl: type[RunTypeT]
    _assistant_impl: type[AssistantTypeT]
    _thread_impl: type[ThreadTypeT]

    async def _create(
        self,
        assistant: str | AssistantTypeT,
        thread: str | ThreadTypeT,
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

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[RunTypeT]:
        page_token_ = get_defined_value(page_token, '')
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


class AsyncRuns(BaseRuns[AsyncRun, AsyncAssistant, AsyncThread]):
    _run_impl = AsyncRun
    _assistant_impl = AsyncAssistant
    _thread_impl = AsyncThread

    # NB: there is no public 'create'
    get = BaseRuns._get
    list = BaseRuns._list


class Runs(BaseRuns[Run, Assistant, Thread]):
    _run_impl = Run
    _assistant_impl = Assistant
    _thread_impl = Thread

    # NB: there is no public 'create'
    get = run_sync(BaseRuns._get)
    list = run_sync_generator(BaseRuns._list)
