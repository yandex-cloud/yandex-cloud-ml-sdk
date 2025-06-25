# pylint: disable=protected-access
from __future__ import annotations

import json

import pytest
import pytest_asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._models.completions.model import BaseGPTModel
from yandex_cloud_ml_sdk._threads.thread import AsyncThread

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='text')
def fixture_text() -> str:
    return 'collect all numbers from: 5, 4, a, 1'


@pytest.fixture(name='model')
def fixture_model(async_sdk: AsyncYCloudML) -> BaseGPTModel:
    return async_sdk.models.completions('yandexgpt', model_version='latest')


@pytest_asyncio.fixture(name='thread')
async def fixture_thread(async_sdk: AsyncYCloudML, text: str) -> AsyncThread:
    thread = await async_sdk.threads.create()
    await thread.write(text)
    return thread


@pytest.mark.allow_grpc
async def test_structured_output_simple_json(
    async_sdk: AsyncYCloudML, thread: AsyncThread, model: BaseGPTModel
) -> None:
    assistant = await async_sdk.assistants.create(model, response_format='json')

    run = await assistant.run(thread)
    result = await run

    assert json.loads(result.text) == {"output": "5, 4, 1"}

    with pytest.raises(TypeError):
        await assistant.update(response_format=True)  # type: ignore[arg-type]


@pytest.mark.require_env('pydantic')
@pytest.mark.allow_grpc
async def test_structured_output_pydantic_model(
    async_sdk: AsyncYCloudML, thread: AsyncThread, model: BaseGPTModel
) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    class Numbers(pydantic.BaseModel):
        numbers: list[int]

    assistant = await async_sdk.assistants.create(model, response_format=Numbers)
    run = await assistant.run(thread)
    result = await run

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.require_env('pydantic')
@pytest.mark.allow_grpc
async def test_structured_output_pydantic_dataclass(
    async_sdk: AsyncYCloudML, thread: AsyncThread, model: BaseGPTModel
) -> None:
    import pydantic  # pylint: disable=import-outside-toplevel

    @pydantic.dataclasses.dataclass
    class Numbers:
        numbers: list[int]

    assistant = await async_sdk.assistants.create(model, response_format=Numbers)
    run = await assistant.run(thread)
    result = await run
    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.allow_grpc
async def test_structured_output_json_schema(
    async_sdk: AsyncYCloudML, thread: AsyncThread, model: BaseGPTModel
) -> None:
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

    assistant = await async_sdk.assistants.create(
        model,
        response_format={'json_schema': schema}  # type: ignore[arg-type,typeddict-item]
    )
    run = await assistant.run(thread)
    result = await run

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}


@pytest.mark.allow_grpc
async def test_custom_structured_output_json_schema(
    async_sdk: AsyncYCloudML, thread: AsyncThread, model: BaseGPTModel, text: str
) -> None:
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

    assistant = await async_sdk.assistants.create(
        model,
    )
    run = await assistant.run(thread)
    result = await run

    try:
        json.loads(result.text)
    except json.JSONDecodeError:
        pass
    else:
        assert False

    await thread.write(text)
    run = await assistant.run(
        thread,
        custom_response_format={'json_schema': schema}  # type: ignore[arg-type,typeddict-item]
    )
    result = await run

    assert json.loads(result.text) == {'numbers': [5, 4, 1]}
