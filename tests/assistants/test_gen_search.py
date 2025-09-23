from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk._sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._tools.generative_search import GenerativeSearchTool

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
async def test_base_gen_search(
    async_sdk: AsyncYCloudML,
    clear_deleteable_resources,  # pylint: disable=unused-argument
) -> None:
    """
    Gen search tool is doing some magic which is unobservable by run result.
    So, I'm checking only creating/parsing assistant with such tool.

    What about testing of bad gen search parameters - it is already tested in search domain.
    """

    description = "test_base_gen_search"

    for kwargs in (
        {'host': 'ya.ru'},
        {'site': 'https://ya.ru'},
        {'url': 'https://ya.ru'},
        {'enable_nrfm_docs': True},
        {'search_filters': [{'date': '>20150101'}]}
    ):
        tool = async_sdk.tools.generative_search(description=description, **kwargs)
        assistant = await async_sdk.assistants.create('yandexgpt', tools=[tool])

        second_assistant = await async_sdk.assistants.get(assistant.id)
        assert second_assistant.tools
        assert len(second_assistant.tools) == 1
        second_tool = second_assistant.tools[0]
        assert isinstance(second_tool, GenerativeSearchTool)

        for field in ('site', 'host', 'url', 'description', 'enable_nrfm_docs', 'search_filters'):
            value_l = getattr(tool, field)
            value_r = getattr(second_tool, field)

            assert bool(value_r) == bool(value_l)

            if value_l:
                assert value_l == value_r

            if field in kwargs:
                assert value_l
