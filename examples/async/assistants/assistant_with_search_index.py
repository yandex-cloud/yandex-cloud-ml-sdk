#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    file_coros = (
        sdk.files.upload(
            local_path(path),
            ttl_days=5,
            expiration_policy="static",
        )
        for path in ['turkey_example.txt', 'maldives_example.txt']
    )

    files = await asyncio.gather(*file_coros)
    operation = await sdk.search_indexes.create_deferred(files)
    search_index = await operation

    tool = sdk.tools.search_index(search_index)

    assistant = await sdk.assistants.create('yandexgpt', tools=[tool])
    thread = await sdk.threads.create()

    search_query = local_path('search_query.txt').read_text().splitlines()[0]
    await thread.write(search_query)
    run = await assistant.run(thread)

    # poll_inteval is 0.5s by default, but you could lower it to optimize
    # wait time
    result = await run.wait(poll_interval=0.05)
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
    await thread.write(search_query)

    # You could also use run_stream method to start gettig response parts
    # as soon it will be generated
    run = await assistant.run_stream(thread)
    print('Question:', search_query)
    async for event in run:
        print("Answer part:", event.text)
        print("Answer status:", event.status)

    await search_index.delete()
    await thread.delete()
    await assistant.delete()

    for file in files:
        await file.delete()


if __name__ == '__main__':
    asyncio.run(main())
