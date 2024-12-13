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

    search_query = local_path('search_query.txt').read_text().splitlines()[0]
    thread.write(search_query)
    run = assistant.run(thread)

    # poll_inteval is 0.5s by default, but you could lower it to optimize
    # wait time
    result = run.wait(poll_interval=0.05)
    print('Question:', search_query)
    print('Answer:', result.text)

    search_query = "Cколько пошлина в Анталье"
    thread.write(search_query)

    # You could also use run_stream method to start gettig response parts
    # as soon it will be generated
    run = assistant.run_stream(thread)
    print('Question:', search_query)
    for event in run:
        print("Answer part:", event.text)
        print("Answer status:", event.status)

    search_index.delete()
    thread.delete()
    assistant.delete()

    for file in files:
        file.delete()


if __name__ == '__main__':
    main()
