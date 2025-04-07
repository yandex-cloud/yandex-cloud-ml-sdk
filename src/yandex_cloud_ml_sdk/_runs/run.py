# pylint: disable=no-name-in-module,protected-access
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, TypeVar, cast

from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.runs.run_pb2 import Run as ProtoRun
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import AttachRunRequest, GetRunRequest, ListenRunRequest
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2_grpc import RunServiceStub

from yandex_cloud_ml_sdk._assistants.prompt_truncation_options import PromptTruncationOptions
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall, ToolCall, ToolCallTypeT
from yandex_cloud_ml_sdk._tools.tool_result import (
    ProtoAssistantToolResultList, ToolResultInputType, tool_results_to_proto
)
from yandex_cloud_ml_sdk._types.operation import OperationInterface
from yandex_cloud_ml_sdk._types.resource import BaseResource
from yandex_cloud_ml_sdk._types.result import ProtoMessage
from yandex_cloud_ml_sdk._utils.proto import get_google_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .result import RunResult, RunStreamEvent
from .status import RunStatus

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseRun(BaseResource, OperationInterface[RunResult[ToolCallTypeT]]):
    id: str
    assistant_id: str
    thread_id: str
    created_by: str
    created_at: datetime
    labels: dict[str, str] | None
    custom_temperature: float | None
    custom_max_tokens: int | None
    custom_prompt_truncation_options: PromptTruncationOptions | None

    @property
    def custom_max_prompt_tokens(self) -> int | None:
        if self.custom_prompt_truncation_options:
            return self.custom_prompt_truncation_options.max_prompt_tokens
        return None

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessage, sdk: BaseSDK) -> dict[str, Any]:
        proto = cast(ProtoRun, proto)
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)

        kwargs.update({
            'custom_temperature': get_google_value(proto.custom_completion_options, 'temperature', None, float),
            'custom_max_tokens': get_google_value(proto.custom_completion_options, 'max_tokens', None, int),
        })
        if proto.HasField('custom_prompt_truncation_options'):
            kwargs['custom_prompt_truncation_options'] = PromptTruncationOptions._from_proto(
                proto=proto.custom_prompt_truncation_options,
                sdk=sdk
            )

        return kwargs

    async def _get_run(self, *, timeout: float = 60) -> ProtoRun:
        request = GetRunRequest(run_id=self.id)

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoRun,
            )

        return response

    async def _get_status(self, *, timeout: float = 60) -> RunStatus:  # type: ignore[override]
        run = await self._get_run(timeout=timeout)

        return RunStatus._from_proto(proto=run.state.status)

    async def _get_result(self, *, timeout: float = 60) -> RunResult[ToolCallTypeT]:
        run = await self._get_run(timeout=timeout)

        return RunResult._from_proto(sdk=self._sdk, proto=run)

    async def _listen(
        self,
        *,
        events_start_idx: int = 0,
        timeout: float = 60,
    ) -> AsyncIterator[RunStreamEvent[ToolCallTypeT]]:
        request = ListenRunRequest(
            run_id=self.id,
            events_start_idx=Int64Value(value=events_start_idx),
        )

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.Listen,
                request,
                timeout=timeout,
                expected_type=ProtoStreamEvent,
            ):
                yield RunStreamEvent._from_proto(proto=response, sdk=self._sdk)

        return

    async def _attach_run_impl(
        self,
        requests: AsyncIterator[AttachRunRequest],
        *,
        timeout: float = 60,
    ) -> AsyncIterator[ProtoStreamEvent]:
        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            async for response in self._client.stream_service_stream(
                stub.Attach,
                requests,
                timeout=timeout,
                expected_type=ProtoStreamEvent
            ):
                yield response

        return

    async def _submit_tool_results(
        self,
        tool_results: ToolResultInputType,
        *,
        timeout: float = 60,
    ) -> None:
        proto_results = tool_results_to_proto(tool_results, proto_type=ProtoAssistantToolResultList)
        request = AttachRunRequest(
            run_id=self.id,
            tool_result_list=proto_results,
        )

        async def requests() -> AsyncIterator[AttachRunRequest]:
            yield request

        i = 0
        async for _ in self._attach_run_impl(requests(), timeout=timeout):
            i += 1
            # NB First event - is a history TOOL_CALS event.
            # But we need to be sure that Run on server side had enough time to change it status
            # from TOOL_CALLS to make Run object reliably usable by user, so we wait "next event".
            # TODO: Don't use Attach, use SubmitToRun handle.
            if i == 2:
                return

        return


class AsyncRun(BaseRun[AsyncToolCall]):
    async def get_status(self, *, timeout: float = 60) -> RunStatus:
        return await self._get_status(timeout=timeout)

    async def get_result(self, *, timeout: float = 60) -> RunResult[AsyncToolCall]:
        return await self._get_result(timeout=timeout)

    async def listen(
        self,
        *,
        events_start_idx: int = 0,
        timeout: float = 60,
    ) -> AsyncIterator[RunStreamEvent[AsyncToolCall]]:
        async for event in self._listen(
            events_start_idx=events_start_idx,
            timeout=timeout,
        ):
            yield event

    __aiter__ = listen

    async def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 300,
        poll_interval: float = 0.5,
    ) -> RunResult[AsyncToolCall]:
        return await self._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def __await__(self):
        return self.wait().__await__()

    async def submit_tool_results(
        self,
        tool_results: ToolResultInputType,
        *,
        timeout: float = 60,
    ) -> None:
        await super()._submit_tool_results(tool_results=tool_results, timeout=timeout)


class Run(BaseRun[ToolCall]):
    __get_status = run_sync(BaseRun._get_status)
    __get_result = run_sync(BaseRun._get_result)
    __wait = run_sync(BaseRun._wait)
    __listen = run_sync_generator(BaseRun._listen)
    __iter__ = __listen
    __submit_tool_results = run_sync(BaseRun._submit_tool_results)

    def get_status(self, *, timeout: float = 60) -> RunStatus:
        return self.__get_status(timeout=timeout)

    def get_result(self, *, timeout: float = 60) -> RunResult[ToolCall]:
        return self.__get_result(timeout=timeout)

    def listen(
        self,
        *,
        events_start_idx: int = 0,
        timeout: float = 60,
    ) -> Iterator[RunStreamEvent[ToolCall]]:
        yield from self.__listen(
            events_start_idx=events_start_idx,
            timeout=timeout,
        )

    def wait(
        self,
        *,
        timeout: float = 60,
        poll_timeout: int = 300,
        poll_interval: float = 0.5,
    ) -> RunResult[ToolCall]:
        # NB: mypy can't unterstand normally __wait return type and thinks its ResultTypeT
        return self.__wait(  # type: ignore[return-value]
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )

    def submit_tool_results(
        self,
        tool_results: ToolResultInputType,
        *,
        timeout: float = 60,
    ) -> None:
        self.__submit_tool_results(tool_results=tool_results, timeout=timeout)


RunTypeT = TypeVar('RunTypeT', bound=BaseRun)
