from __future__ import annotations

import pytest

from yandex_ai_studio_sdk import AsyncYCloudML
from yandex_ai_studio_sdk.search_api import (
    FamilyMode, FixTypoMode, GroupMode, Localization, SearchType, SortMode, SortOrder
)


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_web_search_simple_run(async_sdk: AsyncYCloudML) -> None:
    search = async_sdk.search_api.web('ru')

    result = await search.run('yandex cloud')

    assert len(result) >= 1

    for group in result.groups:
        assert len(group) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
@pytest.mark.parametrize(
    'format_,start',
    [('html', b'<!DOCTYPE html>'), ('xml', b'<?xml')]
)
async def test_web_search_simple_raw_run(async_sdk: AsyncYCloudML, format_, start) -> None:
    search = async_sdk.search_api.web('ru')

    result = await search.run('yandex cloud', format=format_)

    assert result.startswith(start)


@pytest.mark.asyncio
@pytest.mark.allow_grpc
async def test_web_search_simple_deferred_run(async_sdk: AsyncYCloudML) -> None:
    search = async_sdk.search_api.web('ru')

    operation = await search.run_deferred('yandex cloud')
    result = await operation

    assert len(result) >= 1

    for group in result.groups:
        assert len(group) >= 1


@pytest.mark.asyncio
@pytest.mark.allow_grpc
@pytest.mark.parametrize(
    'format_,start',
    [('html', b'<!DOCTYPE html>'), ('xml', b'<?xml')]
)
async def test_web_search_simple_deferred_raw_run(async_sdk: AsyncYCloudML, format_, start) -> None:
    search = async_sdk.search_api.web('ru')

    operation = await search.run_deferred('yandex cloud', format=format_)
    result = await operation
    assert result.startswith(start)


def test_web_search_settings(async_sdk: AsyncYCloudML) -> None:
    # pylint: disable=protected-access
    search = async_sdk.search_api.web('RU')
    assert search._config.search_type.name == 'RU'

    same_kwargs = {
        'docs_in_group': 3,
        'groups_on_page': 6,
        'max_passages': 2,
        'region': '225',
        'user_agent': '123',
    }

    search1 = search.configure(
        search_type='kk',
        family_mode='strict',
        fix_typo_mode='off',
        group_mode='deep',
        localization='ru',
        sort_order='desc',
        sort_mode='by_time',
        **same_kwargs,  # type: ignore[arg-type]
    )

    search2 = search.configure(
        search_type=SearchType.KK,
        family_mode=FamilyMode.STRICT,
        fix_typo_mode=FixTypoMode.OFF,
        group_mode=GroupMode.DEEP,
        localization=Localization.RU,
        sort_order=SortOrder.DESC,
        sort_mode=SortMode.BY_TIME,
        **same_kwargs,  # type: ignore[arg-type]
    )

    assert search1._config == search2._config


def test_web_search_validation(async_sdk: AsyncYCloudML) -> None:
    with pytest.raises(ValueError):
        async_sdk.search_api.web('FOO')

    with pytest.raises(ValueError):
        async_sdk.search_api.web(-10)

    with pytest.raises(TypeError):
        async_sdk.search_api.web(search_type={})  # type: ignore[arg-type]

    search = async_sdk.search_api.web('RU')
    with pytest.raises(ValueError):
        search.configure(search_type='FOO')

    with pytest.raises(TypeError):
        search.configure(search_type={})  # type: ignore[arg-type]
