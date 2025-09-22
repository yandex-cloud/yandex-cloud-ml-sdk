# pylint: disable=no-name-in-module
from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence, overload

from yandex_cloud_ml_sdk._models.completions.result import AlternativeStatus, Usage
from yandex_cloud_ml_sdk._tools.tool_call import HaveToolCalls, ToolCallTypeT
from yandex_cloud_ml_sdk._tools.tool_call_list import HttpToolCallList
from yandex_cloud_ml_sdk._types.json import JsonBased
from yandex_cloud_ml_sdk._types.message import TextMessage
from yandex_cloud_ml_sdk._types.result import BaseJsonResult, SDKType

YCMLSDK_PREFIX = 'ycmlsdk'
YCMLSDK_TOOL_CALLS = f'{YCMLSDK_PREFIX}_tool_calls'
YCMLSDK_TEXT = f'{YCMLSDK_PREFIX}_text'
YCMLSDK_REASONING_TEXT = f'{YCMLSDK_PREFIX}_reasoning_text'


class ChatUsage(Usage):
    @property
    def prompt_tokens(self) -> int:
        return self.input_text_tokens


class FinishReason(Enum):
    STOP = 'stop'
    LENGTH = 'length'
    CONTENT_FILTER = 'content_filter'
    TOOL_CALLS = 'tool_calls'
    NULL = 'null'
    USAGE = 'usage'

    @classmethod
    def _coerce(cls, value: str | None):
        if value is None:
            return cls('null')
        return cls(value.lower())


STATUS_TABLE = {
    FinishReason.STOP: AlternativeStatus.FINAL,
    FinishReason.LENGTH: AlternativeStatus.TRUNCATED_FINAL,
    FinishReason.CONTENT_FILTER: AlternativeStatus.CONTENT_FILTER,
    FinishReason.TOOL_CALLS: AlternativeStatus.TOOL_CALLS,
    FinishReason.NULL: AlternativeStatus.PARTIAL,
    FinishReason.USAGE: AlternativeStatus.USAGE,
}


@dataclass(frozen=True)
class ChatChoice(TextMessage, HaveToolCalls[ToolCallTypeT], JsonBased):
    finish_reason: FinishReason
    status: AlternativeStatus
    tool_calls: HttpToolCallList[ToolCallTypeT] | None
    reasoning_text: str | None

    @property
    def content(self) -> str:
        return self.text

    @property
    def reasoning_content(self) -> str | None:
        return self.reasoning_text

    @classmethod
    def _from_json(cls, *, data: dict[str, Any], sdk: SDKType) -> ChatChoice:
        if 'delta' in data:
            return DeltaChatChoice._from_json(data=data, sdk=sdk)

        finish_reason = FinishReason._coerce(data.get('finish_reason'))
        status = STATUS_TABLE[finish_reason]

        message = data['message']
        role = message['role']
        text = message['content']
        reasoning_text = message.get('reasoning_content')

        tool_calls = None
        if raw_tool_calls := message.get('tool_calls'):
            tool_calls = HttpToolCallList._from_json(data=raw_tool_calls, sdk=sdk)

        return cls(
            text=text,
            role=role,
            finish_reason=finish_reason,
            status=status,
            reasoning_text=reasoning_text,
            tool_calls=tool_calls,
        )


@dataclass(frozen=True)
class DeltaChatChoice(ChatChoice[ToolCallTypeT]):
    delta: str
    reasoning_delta: str | None

    @classmethod
    def _from_json(cls, *, data: dict[str, Any], sdk: SDKType) -> DeltaChatChoice[ToolCallTypeT]:
        delta_dict = data.get('delta', {})

        delta = delta_dict.get('content', '')
        text = delta_dict.get(YCMLSDK_TEXT, '')
        role = delta_dict.get('role', 'unknown')

        reasoning_text = delta_dict.get(YCMLSDK_REASONING_TEXT)
        reasoning_delta = delta_dict.get('reasoning_content')

        finish_reason = FinishReason._coerce(data.get('finish_reason'))
        status = STATUS_TABLE[finish_reason]

        tool_calls = None
        if raw_tool_calls := delta_dict.get(YCMLSDK_TOOL_CALLS):
            tool_calls = HttpToolCallList._from_json(data=raw_tool_calls, sdk=sdk)

        return cls(
            delta=delta,
            text=text,
            role=role,
            finish_reason=finish_reason,
            status=status,
            reasoning_text=reasoning_text,
            reasoning_delta=reasoning_delta,
            tool_calls=tool_calls
        )



@dataclass(frozen=True)
class ChatModelResult(BaseJsonResult, Sequence, HaveToolCalls[ToolCallTypeT]):
    choices: tuple[ChatChoice[ToolCallTypeT], ...]
    usage: ChatUsage | None

    created: datetime.datetime
    model: str
    id: str

    @property
    def alternatives(self) -> tuple[ChatChoice[ToolCallTypeT], ...]:
        return self.choices

    @classmethod
    def _from_json(cls, *, data: dict[str, Any], sdk: SDKType) -> ChatModelResult:
        choices = tuple(ChatChoice._from_json(data=choice, sdk=sdk) for choice in data['choices'])
        usage: ChatUsage | None = None
        if raw_usage := data.get('usage'):
            usage = ChatUsage(
                input_text_tokens=raw_usage['prompt_tokens'],
                completion_tokens=raw_usage['completion_tokens'],
                total_tokens=raw_usage['total_tokens']
            )

        return cls(
            choices=choices,
            usage=usage,
            created=datetime.datetime.utcfromtimestamp(data['created']),
            model=data['model'],
            id=data['id']
        )


    def __len__(self):
        return len(self.alternatives)

    @overload
    def __getitem__(self, index: int, /) -> ChatChoice:
        pass

    @overload
    def __getitem__(self, slice_: slice, /) -> tuple[ChatChoice, ...]:
        pass

    def __getitem__(self, index, /):
        return self.choices[index]

    @property
    def role(self) -> str:
        return self[0].role

    @property
    def content(self) -> str:
        return self[0].content

    @property
    def text(self) -> str:
        return self[0].text

    @property
    def reasoning_text(self) -> str | None:
        return self[0].reasoning_text

    @property
    def reasoning_content(self) -> str | None:
        return self[0].reasoning_content

    @property
    def status(self) -> AlternativeStatus:
        return self[0].status

    @property
    def finish_reason(self) -> FinishReason:
        return self[0].finish_reason

    @property
    def tool_calls(self) -> HttpToolCallList[ToolCallTypeT] | None:
        return self[0].tool_calls
