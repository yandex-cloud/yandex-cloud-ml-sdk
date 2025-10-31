#!/usr/bin/env python3

from __future__ import annotations

from typing import Literal, cast

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    search = sdk.search_api.web('RU')

    format_ = input('Choose format ([xml]/html): ')
    format_ = format_.strip() or 'xml'
    assert format_.lower() in ('xml', 'html')
    format_ = cast(Literal['html', 'xml'], format_)

    search_query = input('Enter the search query: ')
    if not search_query.strip():
        search_query = 'Yandex Cloud'

    search_result = search.run(search_query, format=format_)
    assert isinstance(search_result, bytes)

    print(search_result.decode('utf-8'))

    for page in range(1, 10):
        print(f'Page {page}:')
        # unlike simple_run.py example you need to parse a result by yourself to
        # decide if there are any results or not
        search_result = search.run(search_query, format=format_, page=page)
        print(search_result.decode('utf-8'))
        print()


if __name__ == '__main__':
    main()
