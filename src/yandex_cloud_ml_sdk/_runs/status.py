# pylint: disable=no-name-in-module
from __future__ import annotations

from enum import IntEnum

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import RunState as ProtoRunState
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent

from yandex_cloud_ml_sdk._types.operation import BaseOperationStatus
from yandex_cloud_ml_sdk._utils.proto import ProtoEnumBase


# pylint: disable=abstract-method
class BaseRunStatus(BaseOperationStatus):
    """
    Base class for run status enumerations.
    """


class RunStatus(BaseRunStatus, ProtoEnumBase, IntEnum):
    """
    Enumeration of possible run statuses.
    """
    #: Unknown status (-1)
    UNKNOWN = -1
    #: Status not specified
    RUN_STATUS_UNSPECIFIED = ProtoRunState.RUN_STATUS_UNSPECIFIED
    #: Status not specified
    PENDING = ProtoRunState.PENDING
    #: Run is in progress
    IN_PROGRESS = ProtoRunState.IN_PROGRESS
    #: Run has failed
    FAILED = ProtoRunState.FAILED
    #: Run completed successfully
    COMPLETED = ProtoRunState.COMPLETED
    #: Run requires tool calls
    TOOL_CALLS = ProtoRunState.TOOL_CALLS

    @property
    def is_running(self) -> bool:
        """
        Check if execution is still in progress.
        """
        return self in (self.IN_PROGRESS, self.PENDING)

    @property
    def is_succeeded(self) -> bool:
        """
        Check if execution completed successfully.
        """
        return self in (self.COMPLETED, self.TOOL_CALLS)

    @property
    def is_failed(self) -> bool:
        """
        Check if execution failed.
        """
        return self is self.FAILED


class StreamEvent(BaseRunStatus, ProtoEnumBase, IntEnum):
    """
    Enumeration of possible stream events during run execution.
    """
    #: Unknown event type (-1)
    UNKNOWN = -1
    #: Event type not specified
    EVENT_TYPE_UNSPECIFIED = ProtoStreamEvent.EVENT_TYPE_UNSPECIFIED
    #: Partial message content
    PARTIAL_MESSAGE = ProtoStreamEvent.PARTIAL_MESSAGE
    #: Error occurred
    ERROR = ProtoStreamEvent.ERROR
    #: Execution completed
    DONE = ProtoStreamEvent.DONE
    #: Tool calls required
    TOOL_CALLS = ProtoStreamEvent.TOOL_CALLS

    @property
    def is_running(self) -> bool:
        """
        Check if execution is still in progress.
        """
        return self is self.PARTIAL_MESSAGE

    @property
    def is_succeeded(self) -> bool:
        """
        Check if execution completed successfully.
        """
        return self in (self.DONE, self.TOOL_CALLS)

    @property
    def is_failed(self) -> bool:
        """
        Check if execution failed.
        """
        return self is self.ERROR
