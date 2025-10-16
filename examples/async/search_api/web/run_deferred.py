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

    operation = await search.run_deferred(search_query)
    # More on how to work with "search_result" objects at
    # run_simple.py
    search_result = await operation.wait(poll_interval=1)
    print(f'{len(search_result.docs)} documents found on page #{0}')

    # Search result have a helper to request a next page:
    operation = await search_result.next_page_deferred()
    search_result = await operation.wait(poll_interval=1)
    print(f'{len(search_result.docs)} documents found on page #{1}')

    # More on how to work with "raw" formats at run_raw.py example;
    # here is only about run_deferred
    operation_xml = await search.run_deferred(search_query, format='xml')
    # You could poll operation more often:
    bytes_search_result = await operation_xml.wait(poll_interval=1)
    print(f'{len(bytes_search_result)} bytes in resulting xml for page #{0}')

    # there is no helpers to request next page for raw format:
    operation_xml = await search.run_deferred(search_query, format='xml', page=1)
    bytes_search_result = await operation_xml.wait(poll_interval=1)
    print(f'{len(bytes_search_result)} bytes in resulting xml for page #{1}')


if __name__ == '__main__':
    asyncio.run(main())
