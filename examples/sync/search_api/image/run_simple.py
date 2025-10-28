#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    search = sdk.search_api.image('RU')

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    search_result = search.run(search_query)

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
        search_result = search_result.next_page()


if __name__ == '__main__':
    main()
