#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_api import FamilyMode

EXAMPLE_FILE = pathlib.Path(__file__).parent / 'image.jpeg'


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # You could pass initial configuration here:
    search = sdk.search_api.by_image(
        family_mode="moderate",
        site="ya.ru",
    )
    # Or configure the search object later:
    search = search.configure(
        # family mode could be passed as a string or special enum value
        family_mode=FamilyMode.NONE,
    )

    # You could reset any config value back to default by passing None:
    search = search.configure(
        site=None
    )

    # First option is a search from bytes data:
    image_data = pathlib.Path(EXAMPLE_FILE).read_bytes()
    search_result = await search.run(image_data)

    # You could exam search_result structure via pprint to know how to work with it
    # pprint.pprint(search_result)
    # search result could be used in boolean context:
    if search_result:
        print(f'{len(search_result)} documents found')
    else:
        print('Nothing found')

    # Photo of Leo Tolstoy
    url = "https://upload.wikimedia.org/wikipedia/commons/b/be/Leo_Tolstoy_1908_Portrait_%283x4_cropped%29.jpg"
    # Second option is a search from remote image url:
    search_result = await search.run_from_url(url)

    # Third option is search with CBIR ID: it is way faster
    # than any other option but requires to make at least one
    # "heavy" request to get this ID.
    cbid_id = search_result.cbir_id
    search_result = await search.run_from_id(cbid_id, page=1)

    while search_result:
        print(f'Page {search_result.page}:')
        for document in search_result:
            print(document)

        # search_result.next_page() is a shortcut for
        # .run_from_id(search_query.cbir_id, page=page + 1)
        # with search configuration saved from initial run;
        # last page + 1 will return an "empty" search_result;
        search_result = await search_result.next_page()


if __name__ == '__main__':
    asyncio.run(main())
