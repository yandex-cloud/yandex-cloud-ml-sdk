# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='tool')
def fixture_tool(async_sdk: AsyncYCloudML):
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

    return async_sdk.tools.function(
        schema,  # type: ignore[arg-type]
        name='special_operation',
        description="Tool which have to collect all the numbers from user message and do a FOO with it",
    )


@pytest.mark.skip(reason="bidirectional streams is not supported with our system of cassetes")
@pytest.mark.allow_grpc
async def test_sync_function_call(async_sdk: AsyncYCloudML, tool):
    assistant = await async_sdk.assistants.create('yandexgpt', tools=tool)
    thread = await async_sdk.threads.create()
    await thread.write('do a FOO with all the numbers from: 5, 4, a, 1')

    run = await assistant.run(thread)
    result = await run

    assert result.status.name == 'TOOL_CALLS'
    assert len(result.tool_calls) == 1
    function = result.tool_calls[0].function
    assert function
    assert function.name == 'special_operation'
    numbers = function.arguments['numbers']
    assert numbers == [5.0, 4.0, 1.0]
    assert all(isinstance(number, float) for number in numbers)

    await run.submit_tool_results({'name': 'special_operation', 'content': '+20.0'})

    result = await run
    assert result.status.name == 'COMPLETED'
    assert result.text
    assert '+20' in result.text
    assert result.tool_calls is None

    await assistant.delete()
    await thread.delete()


@pytest.mark.skip("TODO: run.listen is somewhy is not working in this example")
@pytest.mark.allow_grpc
async def test_stream_function_call(async_sdk: AsyncYCloudML, tool):
    model = async_sdk.models.completions('yandexgpt', model_version='rc')
    assistant = await async_sdk.assistants.create(model, tools=tool)
    thread = await async_sdk.threads.create()

    await thread.write('do a FOO with all the numbers from: 5, 4, a, 1')
    run = await assistant.run_stream(thread)

    i = 0
    event = None
    async for event in run:
        i += 1
        if i == 1:
            assert event.status.name == 'TOOL_CALLS'
            assert event.tool_calls
            assert len(event.tool_calls) == 1
            function = event.tool_calls[0].function
            assert function
            assert function.name == 'special_operation'
            numbers = function.arguments['numbers']
            assert numbers == [5.0, 4.0, 1.0]
            assert all(isinstance(number, float) for number in numbers)

            await run.submit_tool_results({'name': 'special_operation', 'content': '+20.0'})

    assert i == 2
    assert event
    assert event.status.name == 'COMPLETED'
    assert event.text
    assert '+20' in event.text
    assert event.tool_calls is None

    await assistant.delete()
    await thread.delete()
