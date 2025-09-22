from __future__ import annotations

import dataclasses
import datetime

import pytest

from yandex_cloud_ml_sdk._chat.completions.message import message_to_json, messages_to_json
from yandex_cloud_ml_sdk._chat.completions.result import (
    AlternativeStatus, ChatChoice, ChatModelResult, DeltaChatChoice, FinishReason, HttpToolCallList
)
from yandex_cloud_ml_sdk._tools.function_call import AsyncFunctionCall
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall
from yandex_cloud_ml_sdk._types.message import TextMessage

RESULT: ChatModelResult = ChatModelResult(
    choices=(
        ChatChoice(
            role='user',
            text="foo",
            finish_reason=FinishReason.STOP,
            reasoning_text=None,
            status=AlternativeStatus.FINAL,
            tool_calls=None
        ),
    ),
    usage=None,
    created=datetime.datetime.now(),
    id="1",
    model="2"
)

DELTA_CHOICE: DeltaChatChoice = DeltaChatChoice(
    delta="o",
    reasoning_delta=None,
    role='user',
    text="foo",
    finish_reason=FinishReason.NULL,
    status=AlternativeStatus.PARTIAL,
    reasoning_text=None,
    tool_calls=None,
)

TOOL_CALL = {'role': 'tool', 'tool_calls': [{"id": "1", "function": {"name": "something"}}]}
RESULT_W_TOOL_CALL = ChatModelResult(
    choices=(
        ChatChoice(
            role='tool',
            finish_reason=FinishReason.TOOL_CALLS,
            text='',
            reasoning_text=None,
            status=AlternativeStatus.TOOL_CALLS,
            tool_calls=HttpToolCallList(
                tool_calls=(
                    AsyncToolCall(
                        id='1',
                        function=AsyncFunctionCall(
                            name="something",
                            arguments={},
                            _proto_origin=None,
                        ),
                        _proto_origin=None,
                        _json_origin=TOOL_CALL['tool_calls'][0],  # type: ignore[arg-type,dict-item]
                    ),
                )
            )
        ),
    ),
    usage=None,
    created=datetime.datetime.now(),
    id="1",
    model="2"
)



@dataclasses.dataclass
class RandomMessageClass:
    role: str
    other_text: str

    @property
    def text(self):
        return self.other_text


@dataclasses.dataclass
class NoRoleClass:
    text: str


@pytest.mark.parametrize(
    "raw_message",
    [
        'foo',
        {'role': 'user', 'text': 'foo'},
        {'role': 'user', 'content': 'foo'},
        TextMessage(role='user', text='foo'),
        RandomMessageClass(role='user', other_text='foo'),
        RESULT,
        DELTA_CHOICE,
    ]
)
def test_messages_single(raw_message) -> None:
    etalon = {"content": "foo", "role": "user"}
    assert message_to_json(raw_message, {}) == etalon
    assert messages_to_json(raw_message) == [etalon]
    assert messages_to_json([raw_message]) == [etalon]
    assert messages_to_json([raw_message, 'bar']) == [etalon, {'content': 'bar', 'role': 'user'}]


def test_no_messages() -> None:
    assert not messages_to_json([])


@pytest.mark.parametrize(
    "bad_message",
    [1, 1.0, NoRoleClass(text="foo")]
)
def bad_message_type(bad_message):
    with pytest.raises(TypeError):
        message_to_json(bad_message, {})

    with pytest.raises(TypeError):
        messages_to_json(bad_message)

    with pytest.raises(TypeError):
        messages_to_json([bad_message])


@pytest.mark.parametrize(
    "bad_message",
    [{}, {"role": "user"}]
)
def bad_message_content(bad_message) -> None:
    with pytest.raises(TypeError):
        message_to_json(bad_message, {})

    with pytest.raises(TypeError):
        messages_to_json(bad_message)

    with pytest.raises(TypeError):
        messages_to_json([bad_message])


@pytest.mark.parametrize(
    "raw_message",
    [
        {"tool_call_id": "foo", "content": "bar"},
        {"tool_call_id": "foo", "content": "bar", "role": "tool"},
    ]
)
def test_chat_tool_result(raw_message) -> None:
    etalon = {"tool_call_id": "foo", "content": "bar", "role": "tool"}
    assert message_to_json(raw_message, {}) == etalon
    assert messages_to_json(raw_message) == [etalon]
    assert messages_to_json([raw_message, 'foo']) == [etalon, {'role': 'user', 'content': 'foo'}]


def test_yandex_tool_result():
    call_result_message = {'tool_results': [{'name': 'something', 'content': '+20.0'}]}
    with pytest.raises(ValueError):
        message_to_json(call_result_message, {})

    etalon = {'role': 'tool', 'content': '+20.0', 'tool_call_id': '1'}
    assert message_to_json(call_result_message, {"something": "1"}) == [etalon]

    with pytest.raises(ValueError):
        messages_to_json(call_result_message)

    assert messages_to_json([TOOL_CALL, call_result_message]) == [TOOL_CALL, etalon]


@pytest.mark.parametrize(
    "tool_call",
    [
        TOOL_CALL,
        RESULT_W_TOOL_CALL,
    ]
)
def test_tool_call(tool_call) -> None:
    assert message_to_json(tool_call, {}) == TOOL_CALL
    assert messages_to_json(tool_call) == [TOOL_CALL]
    assert messages_to_json([tool_call]) == [TOOL_CALL]
