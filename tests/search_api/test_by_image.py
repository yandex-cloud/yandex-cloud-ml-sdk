from __future__ import annotations

import pathlib

import pytest
from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk.search_api import FamilyMode

URL = "https://upload.wikimedia.org/wikipedia/commons/b/be/Leo_Tolstoy_1908_Portrait_%283x4_cropped%29.jpg"


@pytest.fixture(name='image')
def image_fixture() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'image.jpeg'


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_by_image_search_simple_run(async_sdk: AsyncAIStudio, image: pathlib.Path) -> None:
    search = async_sdk.search_api.by_image()
    data = image.read_bytes()

    result = await search.run(data)

    assert len(result) >= 1

    result = await result.next_page()

    assert len(result) >= 1

    result = await search.run_from_id(result.cbir_id)

    assert len(result) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_by_image_search_run_from_url(async_sdk: AsyncAIStudio) -> None:
    search = async_sdk.search_api.by_image()

    result = await search.run_from_url(URL)

    assert len(result) >= 1

    result = await result.next_page()

    assert len(result) >= 1


def test_by_image_search_settings(async_sdk: AsyncAIStudio) -> None:
    # pylint: disable=protected-access
    search = async_sdk.search_api.by_image()

    search1 = search.configure(
        family_mode='strict',
        site='fomo',
    )

    search2 = search.configure(
        family_mode=FamilyMode.STRICT,
        site='fomo',
    )

    assert search1._config == search2._config


def test_by_image_search_validation(async_sdk: AsyncAIStudio) -> None:
    with pytest.raises(TypeError):
        async_sdk.search_api.by_image(family_mode={})  # type: ignore[arg-type]

    search = async_sdk.search_api.by_image()
    with pytest.raises(ValueError):
        search.configure(family_mode='FOO')

    with pytest.raises(TypeError):
        search.configure(family_mode={})  # type: ignore[arg-type]
