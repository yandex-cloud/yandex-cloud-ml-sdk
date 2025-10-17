#!/usr/bin/env python3

from __future__ import annotations

import asyncio
from typing import Literal, cast

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    search = sdk.search_api.web('RU')

    format_ = input('Choose format ([xml]/html): ')
    format_ = format_.strip() or 'xml'
    assert format_.lower() in ('xml', 'html')
    format_ = cast(Literal['html', 'xml'], format_)

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    search_result = await search.run(search_query, format=format_)
    assert isinstance(search_result, bytes)

    print(search_result.decode('utf-8'))

    for page in range(1, 10):
        print(f'Page {page}:')
        # unlike simple_run.py example you need to parse a result by yourself to
        # decide if there are any results or not
        search_result = await search.run(search_query, format=format_, page=page)
        print(search_result.decode('utf-8'))
        print()


if __name__ == '__main__':
    asyncio.run(main())
