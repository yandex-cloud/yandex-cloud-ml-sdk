#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')

    files = []
    for path in ['turkey_example.txt', 'maldives_example.txt']:
        file = sdk.files.upload(
            local_path(path),
            ttl_days=5,
            expiration_policy="static",
        )
        files.append(file)

    operation = sdk.search_indexes.create_deferred(files)
    search_index = operation.wait()

    tool = sdk.tools.search_index(search_index)

    assistant = sdk.assistants.create('yandexgpt', tools=[tool])
    thread = sdk.threads.create()

    for search_query in (
        local_path('search_query.txt').read_text().splitlines()[0],
        "Cколько пошлина в Анталье"
    ):
        thread.write(search_query)
        run = assistant.run(thread)
        result = run.wait()
        print('Question', search_query)
        print('Answer:', result.text)

    search_index.delete()
    thread.delete()
    assistant.delete()

    for file in files:
        file.delete()


if __name__ == '__main__':
    main()
