# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from yandex.cloud.ai.assistants.v1.runs.run_pb2 import Run as ProtoRun
from yandex.cloud.ai.assistants.v1.runs.run_service_pb2 import StreamEvent as ProtoStreamEvent

from yandex_cloud_ml_sdk._messages.message import BaseMessage, Message, PartialMessage
from yandex_cloud_ml_sdk._models.completions.result import Usage
from yandex_cloud_ml_sdk._types.result import BaseResult, ProtoMessage

from .status import BaseRunStatus, RunStatus, StreamEvent

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

StatusTypeT = TypeVar('StatusTypeT', bound=BaseRunStatus)
MessageTypeT = TypeVar('MessageTypeT', bound=BaseMessage)


@dataclasses.dataclass(frozen=True)
class BaseRunResult(
    BaseRunStatus,
    BaseResult,
    Generic[StatusTypeT, MessageTypeT]
):
    status: StatusTypeT
    error: str | None
    _message: MessageTypeT | None

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> BaseRunResult:
        pass

    @property
    def is_running(self) -> bool:
        return self.status.is_running

    @property
    def is_succeeded(self) -> bool:
        return self.status.is_succeeded

    @property
    def is_failed(self) -> bool:
        return self.status.is_failed

    @property
    def message(self) -> MessageTypeT:
        if self.is_failed:
            raise ValueError("run is failed and don't have a message result")
        assert self._message
        return self._message

    @property
    def text(self) -> str:
        return self.message.text

    @property
    def parts(self) -> tuple[Any]:
        return self.message.parts


@dataclasses.dataclass(frozen=True)
class RunResult(BaseRunResult[RunStatus, Message]):
    usage: Usage | None

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> RunResult:
        proto = cast(ProtoRun, proto)
        usage: Usage | None = None

        if proto.HasField('usage'):
            usage = Usage(
                completion_tokens=proto.usage.completion_tokens,
                input_text_tokens=proto.usage.prompt_tokens,
                total_tokens=proto.usage.total_tokens
            )

        state = proto.state

        error: str | None = None
        if state.HasField('error'):
            error = state.error.message

        completed_message: Message | None = None
        if state.HasField('completed_message'):
            completed_message = Message._from_proto(
                sdk=sdk,
                proto=state.completed_message
            )

        # pylint: disable=unexpected-keyword-arg
        return cls(
            status=RunStatus._from_proto(proto.state.status),
            error=error,
            _message=completed_message,
            usage=usage,
        )


@dataclasses.dataclass(frozen=True)
class RunStreamEvent(BaseRunResult[StreamEvent, BaseMessage]):
    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> RunStreamEvent:
        proto = cast(ProtoStreamEvent, proto)
        message: BaseMessage | None = None
        if proto.HasField('partial_message'):
            message = PartialMessage._from_proto(sdk=sdk, proto=proto.partial_message)
        elif proto.HasField('completed_message'):
            message = Message._from_proto(sdk=sdk, proto=proto.completed_message)

        error: str | None = None
        if proto.HasField('error'):
            error = proto.error.message

        # pylint: disable=unexpected-keyword-arg
        return cls(
            status=StreamEvent._from_proto(proto.event_type),
            error=error,
            _message=message,
        )
