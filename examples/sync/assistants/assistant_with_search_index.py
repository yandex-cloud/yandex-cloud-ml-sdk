#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_ai_studio_sdk import AIStudio


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

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

    # You could access .citations attribute for debug purposes
    for citation in result.citations:
        for source in citation.sources:
            # In future there will be more source types
            if source.type != 'filechunk':
                continue
            print('Example source:', source)
            # One source will be enough for example, it takes too much screen space to print
            break
        else:
            continue
        break

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
