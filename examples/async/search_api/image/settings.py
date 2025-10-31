#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_api import (
    FamilyMode, FixTypoMode, ImageColor, ImageFormat, ImageOrientation, ImageSize, SearchType
)

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Mobile Safari/537.36"

async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    # you could pass any settings when creating search object
    search = sdk.search_api.image(
        'RU',
        family_mode=FamilyMode.MODERATE,
        # By default values in object configation have None as value,
        # which is corresponds to "default" value which is
        # defined on service backend;
        # docs_on_page=None,
    )

    # but also you could reconfigure search object at any time:
    search = search.configure(
        # this is enum-type settings;
        # it could be passed as a string like shown below:
        search_type='kk',
        family_mode='strict',
        fix_typo_mode='off',
        format='jpeg',
        size='LARGE',
        orientation='vertical',
        color='GRAYSCALE',
        # this is usual settings:
        docs_on_page=3,
        site='yandex.ru',
        user_agent=USER_AGENT,
    )

    result = await search.run('yandex cloud')
    print(f'{len(result.docs)} documents on #0 page')

    search = search.configure(
        # also any enum-like option could be passed as explicit
        # enum option;
        # it helps to control and understand which values exists
        search_type=SearchType.RU,
        family_mode=FamilyMode.STRICT,
        fix_typo_mode=FixTypoMode.OFF,
        format=ImageFormat.JPEG,
        size=ImageSize.LARGE,
        orientation=ImageOrientation.VERTICAL,
        color=ImageColor.GRAYSCALE,
        docs_on_page=5,
    )
    result = await search.run('yandex cloud')
    print(f'{len(result.docs)} documents on #0 page')

    search = search.configure(
        # you could revert any config option to default by passing a None value:
        docs_on_page=None,
    )
    result = await search.run('yandex cloud')
    print(f'{len(result.docs)} documents on #0 page')


if __name__ == '__main__':
    asyncio.run(main())
