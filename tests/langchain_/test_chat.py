from __future__ import annotations

import pytest

pytestmark = pytest.mark.require_env('langchain_core')


@pytest.fixture(name='model', params=range(2))
def fixture_model(async_sdk, sdk, request):
    return [async_sdk, sdk][request.param].models.completions('yandexgpt').langchain()


@pytest.fixture(name='chat_history')
def fixture_chat_history():
    from langchain_core.messages import AIMessage, HumanMessage  # pylint: disable=import-outside-toplevel,import-error

    return [
        HumanMessage(content="hello!"),
        AIMessage(content="Hi there human!"),
        HumanMessage(content="Meow!"),
    ]


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_ainvoke(model, chat_history):
    result = await model.ainvoke(chat_history)

    assert result.content == "Meow! How's your day?"


@pytest.mark.allow_grpc
def test_invoke(model, chat_history):
    result = model.invoke(chat_history)

    assert result.content == 'Meow! How are you?'


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_astream(model, chat_history):
    result = [_ async for _ in model.astream(chat_history)]

    assert [r.content for r in result] == ["Me", "ow! Meow meow."]


@pytest.mark.allow_grpc
def test_stream(model, chat_history):
    result = list(model.stream(chat_history))

    assert [r.content for r in result] == ['Me', 'ow, meow!']
