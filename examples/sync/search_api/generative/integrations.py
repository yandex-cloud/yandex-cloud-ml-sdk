#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # NB: This example is totally synthetic to show integrations:
    # 1) We are asking GPT model to formulate a search query
    model = sdk.models.completions('yandexgpt')
    result = model.run('Formulate me a text query to find a description of Bugs Bunny to draw it')

    # 2) We are executing search query at search api
    search = sdk.search_api.generative(site='en.wikipedia.org')
    search_result = search.run(result.text, timeout=600)

    # 3) We are passing search result to a yandex-art with an extra instruction
    image_model = sdk.models.image_generation('yandex-art')
    operation = image_model.run_deferred(["Draw a character by next instruction:", search_result])
    image_result = operation.wait()
    try:
        pathlib.Path('image.jpeg').write_bytes(image_result.image_bytes)
    finally:
        pathlib.Path('image.jpeg').unlink()


if __name__ == '__main__':
    main()
