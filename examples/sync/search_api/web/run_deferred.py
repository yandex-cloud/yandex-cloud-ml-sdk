#!/usr/bin/env python3

from __future__ import annotations

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    search = sdk.search_api.web('RU')

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    operation = search.run_deferred(search_query)
    # More on how to work with "search_result" objects at
    # run_simple.py
    search_result = operation.wait(poll_interval=1)
    print(f'{len(search_result.docs)} documents found on page #{0}')

    # Search result have a helper to request a next page:
    operation = search_result.next_page_deferred()
    search_result = operation.wait(poll_interval=1)
    print(f'{len(search_result.docs)} documents found on page #{1}')

    # More on how to work with "raw" formats at run_raw.py example;
    # here is only about run_deferred
    operation_xml = search.run_deferred(search_query, format='xml')
    # You could poll operation more often:
    bytes_search_result = operation_xml.wait(poll_interval=1)
    print(f'{len(bytes_search_result)} bytes in resulting xml for page #{0}')

    # there is no helpers to request next page for raw format:
    operation_xml = search.run_deferred(search_query, format='xml', page=1)
    bytes_search_result = operation_xml.wait(poll_interval=1)
    print(f'{len(bytes_search_result)} bytes in resulting xml for page #{1}')


if __name__ == '__main__':
    main()
