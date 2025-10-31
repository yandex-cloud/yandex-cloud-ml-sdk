#!/usr/bin/env python3

from __future__ import annotations

import asyncio

from yandex_cloud_ml_sdk import AsyncYCloudML


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

    for i in range(5):
        # unlike simple_run.py example you need to parse a result by yourself to
        # decide if there are any results or not
        search_result = await search.run(search_query, format='xml', page=i)
        print(f'Page {i}:')
        print(search_result.decode('utf-8'))
        print()


if __name__ == '__main__':
    asyncio.run(main())
