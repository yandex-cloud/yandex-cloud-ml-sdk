# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.assistants import AutoPromptTruncationStrategy, LastMessagesPromptTruncationStrategy

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_run(async_sdk: AsyncYCloudML):
    assistant = await async_sdk.assistants.create('yandexgpt')
    thread = await async_sdk.threads.create()
    await thread.write('hey!')
    run = await assistant.run(thread, custom_temperature=0)
    assert run.custom_temperature == 0.0
    assert run.custom_max_tokens is None
    assert run.custom_max_prompt_tokens is None
    assert run.custom_prompt_truncation_options is None
    result = await run

    assert result.is_succeeded
    assert result.status.name == 'COMPLETED'
    assert result.text == 'Hello! How can I help you?'
    assert result.parts == ('Hello! How can I help you?', )
    assert result.error is None
    assert result.usage.completion_tokens > 0

    events = [e async for e in run]
    assert len(events) == 1
    assert events[-1].text == result.text

    await assistant.delete()
    await thread.delete()


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_run_stream(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')
    thread = await async_sdk.threads.create()
    await thread.write('hey!')
    run = await assistant.run_stream(thread, custom_temperature=0)
    result = await run

    assert result.is_succeeded
    assert result.status.name == 'COMPLETED'
    assert result.text == 'Hello! How can I help you?'
    assert result.parts == ('Hello! How can I help you?', )
    assert result.error is None
    assert result.usage.completion_tokens > 0

    events = [e async for e in run]
    assert len(events) == 3
    partial1, partial2, completed = events

    assert partial1.status.name == 'PARTIAL_MESSAGE'
    assert partial1.text == 'Hello'
    assert partial1.error is None

    assert partial2.text == result.text
    assert partial2.status.name == 'PARTIAL_MESSAGE'
    assert partial2.error is None

    assert completed.status.name == 'DONE'
    assert completed.text == result.text
    assert completed.error is None

    await assistant.delete()
    await thread.delete()


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_run_methods(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt')
    thread1 = await async_sdk.threads.create()
    await thread1.write('foo')
    thread2 = await async_sdk.threads.create()
    await thread2.write('bar')

    run1 = await assistant.run(thread1)
    await run1
    run2 = await assistant.run(thread2)
    await run2

    run11 = await async_sdk.runs.get(run1.id)
    assert run1 == run11

    # run22 = await async_sdk.runs.get_last_by_thread(thread2)
    # assert run2 == run22

    # it doesn't work at the moment at the backend
    # all_runs = [r async for r in async_sdk.runs.list()]
    # all_runs_ids = [r.id for r in all_runs]
    # assert run1.id in all_runs_ids
    # assert run2.id in all_runs_ids

    await assistant.delete()
    await thread1.delete()
    await thread2.delete()


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_run_fail(async_sdk):
    assistant = await async_sdk.assistants.create('yandexgpt', max_prompt_tokens=1)
    thread = await async_sdk.threads.create()
    await thread.write('hey! how are you?')
    run = await assistant.run(thread, custom_temperature=0)
    assert run.custom_temperature == 0.0
    assert run.custom_max_tokens is None
    assert run.custom_max_prompt_tokens is None
    assert run.custom_prompt_truncation_options is None
    result = await run

    assert result.is_failed
    assert '1 token' in result.error

    await assistant.delete()
    await thread.delete()


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_custom_run_options(async_sdk: AsyncYCloudML):
    assistant = await async_sdk.assistants.create('yandexgpt')
    thread = await async_sdk.threads.create()
    await thread.write('hey!')
    run = await assistant.run(
        thread,
        custom_temperature=0,
        custom_max_tokens=100,
        custom_max_prompt_tokens=200
    )
    assert run.custom_temperature == 0.0
    assert run.custom_max_tokens == 100
    assert run.custom_max_prompt_tokens == 200
    assert run.custom_prompt_truncation_options
    assert run.custom_prompt_truncation_options.strategy == AutoPromptTruncationStrategy()

    result = await run
    assert result

    run = await assistant.run(
        thread,
        custom_temperature=0,
        custom_prompt_truncation_strategy=LastMessagesPromptTruncationStrategy(num_messages=10),
    )
    assert run.custom_temperature == 0.0
    assert run.custom_max_tokens is None
    assert run.custom_max_prompt_tokens is None
    assert run.custom_prompt_truncation_options
    assert run.custom_prompt_truncation_options.strategy == LastMessagesPromptTruncationStrategy(num_messages=10)

    result = await run
    assert result

    await assistant.delete()
    await thread.delete()
