#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # More about date filter and such you could find at
    # https://yandex.ru/support/search/ru/query-language/search-operators
    search = sdk.search_api.generative(
        site='yandex.cloud',
        search_filters=[
            {'date': '>20250101'},
            {'lang': 'en'},
            {'format': 'pdf'},
        ]
    )

    search_result = await search.run("Yandex cloud cenerative search api params")
    print(search_result)
    # search result will be empty because of there is no pdf documents at yandex.cloud site
    print(f'Found {len(search_result.sources)} sources')

    # You could reconfigure search objects with a new filters:
    search = search.configure(
        search_filters=[
            {'date': '>20250101'},
            {'lang': 'en'},
        ]
    )

    search_result = await search.run("Yandex cloud generative search api params")
    print(f'Found {len(search_result.sources)} sources')

    try:
        search = sdk.search_api.generative(
            search_filters=[
                {'format': 'mp3'},
            ]
        )
    except ValueError:
        available_formats = sdk.search_api.generative.available_formats
        print(f'Note that formats are limited by {available_formats}')
    else:
        assert False, 'This should never happen'


if __name__ == '__main__':
    asyncio.run(main())
