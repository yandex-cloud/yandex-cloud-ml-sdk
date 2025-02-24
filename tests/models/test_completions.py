from __future__ import annotations

import json

import pytest

from yandex_cloud_ml_sdk._models.completions.message import ProtoMessage, TextMessage, messages_to_proto
from yandex_cloud_ml_sdk._models.completions.result import AlternativeStatus
from yandex_cloud_ml_sdk._models.completions.token import Token
from yandex_cloud_ml_sdk._types.misc import UNDEFINED

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='model')
def fixture_model(async_sdk):
    return async_sdk.models.completions('yandexgpt')


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
