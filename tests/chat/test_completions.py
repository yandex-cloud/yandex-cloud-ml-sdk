from __future__ import annotations

import base64
import json
import pathlib
from typing import cast

import httpx._client
import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._chat.completions.result import AlternativeStatus, FinishReason
from yandex_cloud_ml_sdk._types.misc import UNDEFINED
from yandex_cloud_ml_sdk._types.tools.function import FunctionDictType
from yandex_cloud_ml_sdk._types.tools.tool_choice import ToolChoiceType

pytestmark = [pytest.mark.asyncio, pytest.mark.vcr]


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.chat.completions('yandexgpt')


@pytest.fixture(name='model')
def fixture_qwen_model(async_sdk):
    return async_sdk.chat.completions('qwen3-235b-a22b-fp8')


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
        description="Tool which have to collect all the numbers from user message and do a SOMETHING with it"
    )


async def test_run(model):
    result = await model.run('hello')

    assert len(result) == len(result.alternatives) == 1
    assert result[0].role == 'assistant'
    assert result[0].status == AlternativeStatus.FINAL
    assert result[0].text

    assert result.usage.input_text_tokens > 0
    assert result.usage.completion_tokens > 0
    assert result.usage.total_tokens > 0


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
        for r in results[:-2]
    )
    assert all(
        r[0].finish_reason == FinishReason.NULL
        for r in results[:-2]
    )

    assert results[-2].status == AlternativeStatus.FINAL
    assert results[-2].finish_reason == FinishReason.STOP
    assert results[-1].status == AlternativeStatus.USAGE
    assert results[-1].finish_reason == FinishReason.USAGE

    assert all(
        r[0].role == 'assistant' and r[0].text is not None and len(r) == 1
        for r in results
    )

    assert results[-1].usage

    result_text = results[-1].text

    assert ''.join(r[0].delta for r in results) == result_text


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

    def make_request(**kwargs):
        return model._build_request_json(**kwargs)

    assert model._config.reasoning_mode is None
    assert 'reasoning_effort' not in make_request(messages="foo", stream=None)

    model = model.configure(reasoning_mode='LOW')
    assert make_request(messages="foo", stream=None)['reasoning_effort'] == 'low'


async def test_structured_output_simple_json(async_sdk):
    model = async_sdk.chat.completions('yandexgpt')
    model = model.configure(response_format='json', temperature=1)

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {"output": '5, 4, 1'}

    model = model.configure(response_format=True)
    with pytest.raises(TypeError):
        await model.run('collect all numbers from: 5, 4, a, 1')


@pytest.mark.require_env('pydantic')
async def test_structured_output_pydantic_model(async_sdk) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    class Numbers(pydantic.BaseModel):
        numbers: list[int]

    model = async_sdk.chat.completions('yandexgpt')
    model = model.configure(response_format=Numbers)

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.require_env('pydantic')
async def test_structured_output_pydantic_dataclass(async_sdk) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    @pydantic.dataclasses.dataclass
    class Numbers:
        numbers: list[int]

    model = async_sdk.chat.completions('yandexgpt')
    model = model.configure(response_format=Numbers, temperature=0)

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


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

    model = async_sdk.chat.completions('yandexgpt')
    model = model.configure(response_format={'json_schema': schema, "name": 'foo'})

    result = await model.run('collect all numbers from: 5, 4, a, 1')

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


async def test_function_call(async_sdk: AsyncYCloudML, tool) -> None:
    model = async_sdk.chat.completions('yandexgpt')
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
    assert all(isinstance(number, int) for number in numbers)

    call_result = {'tool_results': [{'name': 'something', 'content': '+20.0'}]}
    messages.append(call_result)

    result = await model.run(messages)
    assert result.text
    assert '+20' in result.text
    assert result.tool_calls is None


@pytest.mark.xfail(reason="parallel_tool_calls is not working with openai api right now")
async def test_parallel_function_call(async_sdk: AsyncYCloudML, tool, schema) -> None:
    # pylint: disable=too-many-locals
    tool2 = async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='spooning',
        description="Tool which have to collect all the numbers from user message and do a SPOONING with it",
    )

    model = async_sdk.chat.completions('yandexgpt', model_version='rc')
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
        print(result.tool_calls)
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


@pytest.mark.xfail(reason="parallel_tool_calls is not working with openai api right now")
async def test_tool_choice(async_sdk: AsyncYCloudML, tool, schema) -> None:
    tool2 = async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='something_else',
        description="Tool which have to collect all the numbers from user message and do a SOMETHING with it",
    )

    model = async_sdk.chat.completions('yandexgpt')
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


async def test_multimodal(async_sdk: AsyncYCloudML) -> None:
    model = async_sdk.chat.completions('gemma-3-27b-it')
    image_path = pathlib.Path(__file__).parent / 'example.png'
    image_data = image_path.read_bytes()
    image_base64 = base64.b64encode(image_data)
    image = image_base64.decode('utf-8')

    request = [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text', 'text': "What is depicted in the following image",
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:image/png;base64,{image}'
                    }
                }
            ]
        }
    ]
    result = await model.run(request)
    assert 'complex' in result.text


async def test_extra_query(async_sdk: AsyncYCloudML, monkeypatch) -> None:
    top_k = None

    original = httpx._client.AsyncClient.request

    async def patched_request(*args, **kwargs):
        nonlocal top_k
        top_k = kwargs.get('json', {}).get('top_k')
        return await original(*args, **kwargs)

    monkeypatch.setattr("httpx._client.AsyncClient.request", patched_request)

    query = "Say random number from 0 to 10"

    model = async_sdk.chat.completions('yandexgpt')

    await model.run(query)
    assert not top_k

    model = model.configure(extra_query={'top_k': 3})
    await model.run(query)
    assert top_k == 3


@pytest.mark.parametrize(
    "model_name",
    ['yandexgpt', 'gemma-3-27b-it', 'llama', 'qwen3-235b-a22b-fp8']
)
async def test_stream_function_call(async_sdk: AsyncYCloudML, model_name) -> None:
    calculator_tool = async_sdk.tools.function(
        name="calculator",
        description=(
            "A simple calculator that performs basic arithmetic and @ operations; "
            "call it on ANY arithmetic questions"
        ),
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
                }
            },
            "required": ["expression"],
        },
        strict=True,
    )

    version = 'latest'
    if model_name in ('yandexgpt', 'llama'):
        version = 'rc'
    model = async_sdk.chat.completions(model_name, model_version=version)
    model = model.configure(tools=calculator_tool)

    messages: list = [
        "How much it would be 7@8?",
    ]
    chunk = None

    async for chunk in model.run_stream(messages):
        if chunk.tool_calls:
            tool_call = chunk.tool_calls[0]
            assert tool_call.function
            assert tool_call.function.name == 'calculator'
            assert tool_call.function.arguments == {"expression": '7@8'}

            messages.append(chunk)
            call_result = {'tool_results': [{'name': 'calculator', 'content': '-5'}]}
            messages.append(call_result)

    assert len(messages) == 3

    async for chunk in model.run_stream(messages):
        pass

    assert chunk
    assert chunk.text
    assert '-5' in chunk.text
