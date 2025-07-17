from __future__ import annotations

import json
from typing import cast

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._models.completions.message import ProtoMessage, messages_to_proto
from yandex_cloud_ml_sdk._models.completions.result import AlternativeStatus
from yandex_cloud_ml_sdk._models.completions.token import Token
from yandex_cloud_ml_sdk._types.message import TextMessage
from yandex_cloud_ml_sdk._types.misc import UNDEFINED
from yandex_cloud_ml_sdk._types.tools.function import FunctionDictType
from yandex_cloud_ml_sdk._types.tools.tool_choice import ToolChoiceType

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.models.completions('yandexgpt')


@pytest.fixture(name='schema')
def fixture_schema():
    return {
        "properties": {
            "numbers": {
                "items": {"type": "integer"},
                "title": "Numbers", "type": "array"
            }
        },
        "required": ["numbers"],
        "title": "Numbers", "type": "object"
    }


@pytest.fixture(name='tool')
def fixture_tool(async_sdk, schema):
    return async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='something',
        description="Tool which have to collect all the numbers from user message and do a SOMETHING with it",
    )


@pytest.mark.allow_grpc
async def test_run(model):
    result = await model.run('hello')

    assert len(result) == len(result.alternatives) == 1
    assert result[0].role == 'assistant'
    assert result[0].status == AlternativeStatus.FINAL
    assert result[0].text

    assert result.usage.input_text_tokens > 0
    assert result.usage.completion_tokens > 0
    assert result.usage.total_tokens > 0


@pytest.mark.allow_grpc
async def test_run_stream(model):
    stream = model.run_stream(
        'hello! could you please tell me about platypuses?'
    )

    results = []
    async for result in stream:
        results.append(result)

    assert len(results) > 1

    assert all(
        r[0].status == AlternativeStatus.PARTIAL
        for r in results[:-1]
    )
    assert results[-1][0].status == AlternativeStatus.FINAL

    assert all(
        r[0].role == 'assistant' and r[0].text and len(r) == 1
        for r in results
    )

    completion_tokens = results[0].usage.completion_tokens
    for result in results[1:]:
        assert result.usage.completion_tokens > completion_tokens
        completion_tokens = result.usage.completion_tokens


@pytest.mark.allow_grpc
async def test_chat(model):
    messages = [
        {'role': 'system', 'text': 'Your name is Arkadiy'},
        'Hello! how is your name?'
    ]
    result = await model.run(messages)

    assert 'Arkadiy' in result[0].text

    messages.append(result[0])
    messages.append('My name is Andrew')

    result2 = await model.run(messages)
    messages.append(result2[0])
    messages.append('What is my name?')

    result3 = await model.run(messages)

    assert 'Andrew' in result3[0].text


@pytest.mark.allow_grpc
async def test_run_deferred(model):
    operation = await model.run_deferred('ping')

    result = await operation.wait(poll_interval=0.1)

    assert 'ping' in result[0].text


@pytest.mark.allow_grpc
async def test_tokenize(model):
    result = await model.tokenize('ping')

    assert len(result) > 0
    assert all(isinstance(item, Token) for item in result)


async def test_configure(model):
    # pylint: disable=protected-access
    assert model._config.temperature is None
    assert model._config.max_tokens is None

    model = model.configure(
        temperature=UNDEFINED,
        max_tokens=UNDEFINED
    )

    assert model._config.temperature is None
    assert model._config.max_tokens is None

    model = model.configure(
        temperature=100500,
    )

    assert model._config.temperature == 100500
    assert model._config.max_tokens is None

    model = model.configure(
        temperature=0,
        max_tokens=-1
    )

    assert model._config.temperature == 0
    assert model._config.max_tokens == -1

    with pytest.raises(TypeError):
        model.configure(foo=500)

    assert model._config.reasoning_mode is None
    assert model._make_request(messages="foo", stream=None).completion_options.reasoning_options.mode == 0

    model = model.configure(reasoning_mode='disabled')
    assert model._config.reasoning_mode == 'disabled'
    assert model._make_request(messages="foo", stream=None).completion_options.reasoning_options.mode == 1

    model = model.configure(reasoning_mode='ENABLED_HIDDEN')
    assert model._make_request(messages="foo", stream=None).completion_options.reasoning_options.mode == 2


async def test_messages():
    text_message = 'foo'
    dict_message = {'role': 'somebody', 'text': 'something'}
    class_message = TextMessage(role='1', text='2')

    assert messages_to_proto([text_message]) == [ProtoMessage(role='user', text=text_message)]
    assert messages_to_proto([dict_message]) == [ProtoMessage(role=dict_message['role'], text=dict_message['text'])]
    assert messages_to_proto([class_message]) == [ProtoMessage(role=class_message.role, text=class_message.text)]

    assert messages_to_proto([dict_message, text_message, class_message]) == [
        ProtoMessage(role=dict_message['role'], text=dict_message['text']),
        ProtoMessage(role='user', text=text_message),
        ProtoMessage(role=class_message.role, text=class_message.text),
    ]

    assert not messages_to_proto([])

    with pytest.raises(TypeError):
        messages_to_proto([{}])

    call_result_message = {'tool_results': [{'name': 'something', 'content': '+20.0'}]}
    call_result_message2 = {'tool_results': [{'type': 'function', 'name': 'something', 'content': '+20.0'}]}
    proto_messages = messages_to_proto(call_result_message)
    assert proto_messages == messages_to_proto([call_result_message]) == messages_to_proto(call_result_message2)
    assert proto_messages[0].tool_result_list.tool_results[0].function_result.name == 'something'

    with pytest.raises(TypeError):
        messages_to_proto({'tool_results': [{'type': 'something', 'name': 'something', 'content': '+20.0'}]})

    with pytest.raises(TypeError):
        messages_to_proto({'tool_results': [{'name': 'something'}]})

    with pytest.raises(TypeError):
        messages_to_proto({'tool_results': [{'content': 'something'}]})

    with pytest.raises(TypeError):
        messages_to_proto({'tool_results': {}})


@pytest.mark.allow_grpc
async def test_structured_output_simple_json(async_sdk):
    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(response_format='json')

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {"output": "5, 4, 1"}

    model = model.configure(response_format=True)
    with pytest.raises(TypeError):
        await model.run('collect all numbers from: 5, 4, a, 1')


@pytest.mark.require_env('pydantic')
@pytest.mark.allow_grpc
async def test_structured_output_pydantic_model(async_sdk) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    class Numbers(pydantic.BaseModel):
        numbers: list[int]

    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(response_format=Numbers)

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.require_env('pydantic')
@pytest.mark.allow_grpc
async def test_structured_output_pydantic_dataclass(async_sdk) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    @pydantic.dataclasses.dataclass
    class Numbers:
        numbers: list[int]

    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(response_format=Numbers)

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.allow_grpc
async def test_structured_output_json_schema(async_sdk):
    schema = {
        "properties": {
            "numbers": {
                "items": {"type": "integer"},
                "title": "Numbers", "type": "array"
            }
        },
        "required": ["numbers"],
        "title": "Numbers", "type": "object"
    }

    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(response_format={'json_schema': schema})

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.allow_grpc
async def test_function_call(async_sdk: AsyncYCloudML, tool) -> None:
    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(tools=tool)

    messages: list = [
        'do a SOMETHING with all the numbers from: 5, 4, a, 1'
    ]

    result = await model.run(messages)
    messages.append(result)
    assert result.tool_calls
    assert result.tool_calls is result[0].tool_calls is result.alternatives[0].tool_calls
    assert len(result.tool_calls) == 1
    function = result.tool_calls[0].function
    assert function
    assert function.name == 'something'
    numbers = function.arguments['numbers']
    assert numbers == [5.0, 4.0, 1.0]
    assert all(isinstance(number, float) for number in numbers)

    call_result = {'tool_results': [{'name': 'something', 'content': '+20.0'}]}
    messages.append(call_result)

    result = await model.run(messages)
    assert result.text
    assert '+20' in result.text
    assert result.tool_calls is None


@pytest.mark.allow_grpc
async def test_parallel_function_call(async_sdk: AsyncYCloudML, tool, schema) -> None:
    # pylint: disable=too-many-locals
    tool2 = async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='spooning',
        description="Tool which have to collect all the numbers from user message and do a SPOONING with it",
    )

    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(tools=[tool, tool2])

    message = 'do a SOMETHING and SPOONING with all the numbers from: 5, 4, a, 1'

    for i in (0, 1):
        # 0 for default value before configure
        if i:
            model = model.configure(parallel_tool_calls=True)

        result = await model.run(message)
        assert result.tool_calls
        assert len(result.tool_calls) == 2

        call1, call2 = result.tool_calls[:2]
        assert call1.function
        assert call2.function

        assert call1.function.name == 'something'
        assert call2.function.name == 'spooning'

    model = model.configure(parallel_tool_calls=False)
    messages: list = [message]

    result = await model.run(messages)
    calls: dict[str, int] = {}
    results = {'something': '+20', 'spooning': '-10'}
    i = 0
    while result.tool_calls:
        assert len(result.tool_calls) == 1
        assert result.tool_calls
        call = result.tool_calls[0]
        assert call.function
        name = call.function.name
        calls.setdefault(name, 0)
        calls[name] += 1

        call_result = {'tool_results': [{'name': name, 'content': results[name]}]}
        messages.extend([result, call_result])
        result = await model.run(messages)
        i += 1
        if i == 2:
            break

    assert len(calls) == 2


@pytest.mark.allow_grpc
async def test_tool_choice(async_sdk: AsyncYCloudML, tool, schema) -> None:
    tool2 = async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='something_else',
        description="Tool which have to collect all the numbers from user message and do a SOMETHING with it",
    )

    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    model = model.configure(tools=[tool, tool2], parallel_tool_calls=False)

    message = 'do a SOMETHING and SPOONING with all the numbers from: 5, 4, a, 1'

    tool_choice: ToolChoiceType | None

    for tool_choice in (None, 'required', 'auto'):
        if tool_choice is not None:
            model = model.configure(tool_choice=tool_choice)
        result = await model.run(message)
        assert result.status.name == 'TOOL_CALLS'
        assert result.tool_calls
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].function
        assert result.tool_calls[0].function.name == 'something'

    for tool_choice in (
        tool2,
        cast(FunctionDictType, {'type': 'function', 'function': {'name': 'something_else'}})
    ):
        assert tool_choice is not None
        model = model.configure(tool_choice=tool_choice)
        result = await model.run(message)
        assert result.status.name == 'TOOL_CALLS'
        assert result.tool_calls
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].function
        assert result.tool_calls[0].function.name == 'something_else'

    model = model.configure(tool_choice='none')
    result = await model.run(message)
    assert result.status.name == 'FINAL'

    model = model.configure(tool_choice=None)  # type: ignore[arg-type]
    result = await model.run(message)
    assert result.status.name == 'TOOL_CALLS'


@pytest.mark.parametrize("bad_value", ['foo', {}, 123])
async def test_bad_values_tool_choice(async_sdk, tool, bad_value) -> None:
    model = async_sdk.models.completions('yandexgpt')
    model = model.configure(tools=[tool])

    with pytest.raises((TypeError, ValueError)):
        bad_model = model.configure(tool_choice=bad_value)
        await bad_model.run("doesn't matter")
