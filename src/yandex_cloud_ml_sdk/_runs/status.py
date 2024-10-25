# pylint: disable=no-name-in-module
from __future__ import annotations

import enum

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import RunState as ProtoRunState
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent


class BaseRunStatus:
    @property
    def is_running(self) -> bool:
        raise NotImplementedError()

    @property
    def is_succeeded(self) -> bool:
        raise NotImplementedError()

    @property
    def is_failed(self) -> bool:
        raise NotImplementedError()


class RunStatus(BaseRunStatus, int, enum.Enum):
    UNKNOWN = -1
    RUN_STATUS_UNSPECIFIED = ProtoRunState.RUN_STATUS_UNSPECIFIED
    PENDING = ProtoRunState.PENDING
    IN_PROGRESS = ProtoRunState.IN_PROGRESS
    FAILED = ProtoRunState.FAILED
    COMPLETED = ProtoRunState.COMPLETED

    @property
    def is_running(self) -> bool:
        return self in (self.IN_PROGRESS, self.PENDING)

    @property
    def is_succeeded(self) -> bool:
        return self is self.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self is self.FAILED

    @classmethod
    def _from_proto(cls, proto: int) -> RunStatus:
        try:
            return cls(proto)
        except ValueError:
            return cls(-1)


class StreamEvent(BaseRunStatus, int, enum.Enum):
    UNKNOWN = -1
    EVENT_TYPE_UNSPECIFIED = ProtoStreamEvent.EVENT_TYPE_UNSPECIFIED
    PARTIAL_MESSAGE = ProtoStreamEvent.PARTIAL_MESSAGE
    ERROR = ProtoStreamEvent.ERROR
    DONE = ProtoStreamEvent.DONE

    @property
    def is_running(self) -> bool:
        return self is self.PARTIAL_MESSAGE

    @property
    def is_succeeded(self) -> bool:
        return self is self.DONE

    @property
    def is_failed(self) -> bool:
        return self is self.ERROR

    @classmethod
    def _from_proto(cls, proto: int) -> StreamEvent:
        try:
            return cls(proto)
        except ValueError:
            return cls(-1)
