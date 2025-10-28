from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_api import (
    FamilyMode, FixTypoMode, ImageColor, ImageFormat, ImageOrientation, ImageSize, SearchType
)


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_image_search_simple_run(async_sdk: AsyncYCloudML) -> None:
    search = async_sdk.search_api.image('ru')

    result = await search.run('yandex cloud')

    assert len(result) >= 1

    for group in result.groups:
        assert len(group) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_image_search_simple_raw_run(async_sdk: AsyncYCloudML) -> None:
    search = async_sdk.search_api.image('ru')

    result = await search.run('yandex cloud', format='xml')

    assert result.startswith(b'<?xml')


def test_image_search_settings(async_sdk: AsyncYCloudML) -> None:
    # pylint: disable=protected-access
    search = async_sdk.search_api.image('RU')
    assert search._config.search_type.name == 'RU'

    same_kwargs = {
        'docs_on_page': 3,
        'site': 'fomo',
        'user_agent': '123',
    }

    search1 = search.configure(
        search_type='kk',
        family_mode='strict',
        fix_typo_mode='off',
        format='jpeg',
        size='LARGE',
        orientation='vertical',
        color='GRAYSCALE',
        **same_kwargs,  # type: ignore[arg-type]
    )

    search2 = search.configure(
        search_type=SearchType.KK,
        family_mode=FamilyMode.STRICT,
        fix_typo_mode=FixTypoMode.OFF,
        format=ImageFormat.JPEG,
        size=ImageSize.LARGE,
        orientation=ImageOrientation.VERTICAL,
        color=ImageColor.GRAYSCALE,
        **same_kwargs,  # type: ignore[arg-type]
    )

    assert search1._config == search2._config


def test_image_search_validation(async_sdk: AsyncYCloudML) -> None:
    with pytest.raises(ValueError):
        async_sdk.search_api.image('FOO')

    with pytest.raises(ValueError):
        async_sdk.search_api.image(-10)

    with pytest.raises(TypeError):
        async_sdk.search_api.image(search_type={})  # type: ignore[arg-type]

    search = async_sdk.search_api.image('RU')
    with pytest.raises(ValueError):
        search.configure(search_type='FOO')

    with pytest.raises(TypeError):
        search.configure(search_type={})  # type: ignore[arg-type]
