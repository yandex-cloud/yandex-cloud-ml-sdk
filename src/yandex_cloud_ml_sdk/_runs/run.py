# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, AsyncIterator

from google.protobuf.wrappers_pb2 import Int64Value
from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.runs.run_pb2 import Run as ProtoRun
from yandex.cloud.ai.assistants.v1.runs.run_pb2 import RunState as ProtoRunState
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import GetRunRequest, ListenRunRequest
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2_grpc import RunServiceStub

from yandex_cloud_ml_sdk._types.misc import UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.operation import OperationInterface
from yandex_cloud_ml_sdk._types.resource import BaseResource
from yandex_cloud_ml_sdk._utils.proto import get_google_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .result import RunResult, RunStreamEvent
from .status import RunStatus

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseRun(BaseResource, OperationInterface[RunResult]):
    id: str
    assistant_id: str
    thread_id: str
    created_by: str
    created_at: datetime
    labels: dict[str, str] | None
    usage: Usage | None
    custom_temperature: float | None
    custom_max_tokens: int | None
    custom_max_prompt_tokens: int | None

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoRun, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)

        kwargs.update({
            'custom_temperature': get_google_value(proto.custom_completion_options, 'temperature', None, float),
            'custom_max_tokens': get_google_value(proto.custom_completion_options, 'max_tokens', None, int),
            'custom_max_prompt_tokens': get_google_value(proto.custom_prompt_truncation_options, 'max_prompt_tokens', None, int),
        })

        return kwargs

    async def _get_run(self, *, timeout=60) -> ProtoRun:
        request = GetRunRequest(run_id=self.id)

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoRun,
            )

        return response

    async def _get_status(self, *, timeout=60) -> RunStatus:
        run = await self._get_run(timeout=timeout)

        return RunStatus._from_proto(proto=run.state.status)

    async def _get_result(self, *, timeout=60) -> RunResult:
        run = await self._get_run(timeout=timeout)

        return RunResult._from_proto(sdk=self._sdk, proto=run)

    async def _listen(
        self,
        *,
        events_start_idx: int = 0,
        timeout=60,
    ) -> AsyncIterator[RunStreamEvent]:
        request = ListenRunRequest(
            run_id=self.id,
            events_start_idx=Int64Value(value=events_start_idx),
        )

        async with self._client.get_service_stub(RunServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.Listen,
                request,
                timeout=timeout,
                expected_type=RunStreamEvent,
            ):
                yield RunStreamEvent._from_proto(response, sdk=self._sdk)

        return


class AsyncRun(BaseRun):
    get_status = BaseRun._get_status
    get_result = BaseRun._get_result
    wait = BaseRun._wait
    listen = BaseRun._listen
    __aiter__ = BaseRun._listen

    def __await__(self):
        return self.wait().__await__()


class Run(BaseRun):
    get_status = run_sync(BaseRun._get_status)
    get_result = run_sync(BaseRun._get_result)
    wait = run_sync(BaseRun._wait)
    listen = run_sync_generator(BaseRun._listen)
    __iter__ = run_sync_generator(BaseRun._listen)
