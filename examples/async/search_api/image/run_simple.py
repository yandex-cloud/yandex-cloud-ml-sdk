#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_ai_studio_sdk import AsyncYCloudML


async def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncYCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    search = sdk.search_api.image('RU')

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
        for document in search_result:
            print(document)

        # search_result.next_page() is a shortcut for .run(search_query, page=page + 1)
        # with search configuration saved from initial run;
        # last page + 1 will return an "empty" search_result;
        search_result = await search_result.next_page()


if __name__ == '__main__':
    asyncio.run(main())
