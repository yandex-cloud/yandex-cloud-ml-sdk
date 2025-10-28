#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    search = sdk.search_api.image('RU')

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    for i in range(5):
        # unlike simple_run.py example you need to parse a result by yourself to
        # decide if there are any results or not
        search_result = await search.run(search_query, format='xml', page=i)
        print(f'Page {i}:')
        print(search_result.decode('utf-8'))
        print()


if __name__ == '__main__':
    asyncio.run(main())
