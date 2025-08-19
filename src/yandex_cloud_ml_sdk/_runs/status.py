# pylint: disable=no-name-in-module
from __future__ import annotations

from enum import IntEnum

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import RunState as ProtoRunState
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent

from yandex_cloud_ml_sdk._types.operation import BaseOperationStatus
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase


# pylint: disable=abstract-method
class BaseRunStatus(BaseOperationStatus):
    pass


class RunStatus(BaseRunStatus, ProtoEnumBase, IntEnum):
    UNKNOWN = -1
    RUN_STATUS_UNSPECIFIED = ProtoRunState.RUN_STATUS_UNSPECIFIED
    PENDING = ProtoRunState.PENDING
    IN_PROGRESS = ProtoRunState.IN_PROGRESS
    FAILED = ProtoRunState.FAILED
    COMPLETED = ProtoRunState.COMPLETED
    TOOL_CALLS = ProtoRunState.TOOL_CALLS

    @property
    def is_running(self) -> bool:
        return self in (self.IN_PROGRESS, self.PENDING)

    @property
    def is_succeeded(self) -> bool:
        return self in (self.COMPLETED, self.TOOL_CALLS)

    @property
    def is_failed(self) -> bool:
        return self is self.FAILED


class StreamEvent(BaseRunStatus, ProtoEnumBase, IntEnum):
    UNKNOWN = -1
    EVENT_TYPE_UNSPECIFIED = ProtoStreamEvent.EVENT_TYPE_UNSPECIFIED
    PARTIAL_MESSAGE = ProtoStreamEvent.PARTIAL_MESSAGE
    ERROR = ProtoStreamEvent.ERROR
    DONE = ProtoStreamEvent.DONE
    TOOL_CALLS = ProtoStreamEvent.TOOL_CALLS

    @property
    def is_running(self) -> bool:
        return self is self.PARTIAL_MESSAGE

    @property
    def is_succeeded(self) -> bool:
        return self in (self.DONE, self.TOOL_CALLS)

    @property
    def is_failed(self) -> bool:
        return self is self.ERROR
