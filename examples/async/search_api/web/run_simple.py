#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    search = sdk.search_api.web('RU')

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    search_result = await search.run(search_query)

    # You could exam search_result structure via pprint to know how to work with it
    # pprint.pprint(search_result)

    if not search_result:
        print('Nothing found')

    # search result could be used in boolean context;
    while search_result:
        print(f'Page {search_result.page}:')
        for group in search_result:
            for document in group:
                print(document)

        # search_result.next_page() is a shortcut for .run(search_query, page=page + 1)
        # with search configuration saved from initial run;
        # last page + 1 will return an "empty" search_result;
        search_result = await search_result.next_page()


if __name__ == '__main__':
    asyncio.run(main())
