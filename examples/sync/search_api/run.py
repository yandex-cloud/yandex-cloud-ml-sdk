#!/usr/bin/env python3

from __future__ import annotations

import pprint

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    search = sdk.search_api.generative(
        # You can only use one of site/host/url params
        site=['yandex.cloud', 'yandex.ru'],
        fix_misspell=True,
        enable_nrfm_docs=True,
    )

    # You could pass a string as a query
    search_result = search.run("Yandex cloud cenerative search api params")
    # You could exam search_result structure via pprint to know how to work with it
    pprint.pprint(search_result)
    print()

    queries = [
        # Also you could pass a {'text', 'role'} dict like in comletions models
        {"text": 'Gen search api params', "role": "user"},
        'With examples',
    ]

    # And you could pass an array of any allowed types
    search_result = search.run(queries)  # type: ignore[arg-type]
    print(search_result.text)
    print()

    # Also search result itself could be used as one of the queries for a greater context
    queries.append(search_result)  # type: ignore[arg-type]
    queries.append('Get me more examples of how to use Generative Search API with gprc')

    search_result = search.run(queries)  # type: ignore[arg-type]
    print(search_result.text)
    print()



if __name__ == '__main__':
    main()
