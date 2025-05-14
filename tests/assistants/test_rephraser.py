from __future__ import annotations

import pathlib

import pytest

from yandex_cloud_ml_sdk._sdk import AsyncYCloudML

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
async def test_rephraser_base(
    async_sdk: AsyncYCloudML,
    test_file_path: pathlib.Path,
    clear_deleteable_resources,  # pylint: disable=unused-argument
) -> None:
    thread = await async_sdk.threads.create()

    file = await async_sdk.files.upload(test_file_path)
    operation = await async_sdk.search_indexes.create_deferred(file)
    search_index = await operation.wait()

    tool = async_sdk.tools.search_index(search_index, rephraser=True)
    assistant = await async_sdk.assistants.create('yandexgpt', tools=[tool])

    await thread.write('wats ur mystery')
    run = await assistant.run(thread)
    result = await run

    assert "What mystery would you like to solve?" in result.text

    await thread.write('what is your secret number')
    run = await assistant.run(thread)
    result = await run

    assert result.text == "My secret number is 997."

    await thread.write('wats ur mystery')
    run = await assistant.run(thread)
    result = await run
    assert result.text == "My mystery is my secret number 997."


async def test_rephraser_types(async_sdk: AsyncYCloudML) -> None:
    rephraser = async_sdk.tools.rephraser(True)
    assert rephraser.uri == async_sdk.tools.rephraser('rephraser').uri
    assert rephraser.uri == async_sdk.tools.rephraser(rephraser).uri

    rephraser = async_sdk.tools.rephraser(True, model_version='foo')
    assert '/foo' in rephraser.uri
    assert rephraser.uri == async_sdk.tools.rephraser('rephraser', model_version='foo').uri
    assert rephraser.uri == async_sdk.tools.rephraser(rephraser).uri
