#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

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

    for search_query in (
        local_path('search_query.txt').read_text().splitlines()[0],
        "Cколько пошлина в Анталье"
    ):
        await thread.write(search_query)
        run = await assistant.run(thread)
        result = await run
        print('Question', search_query)
        print('Answer:', result.text)

    await search_index.delete()
    await thread.delete()
    await assistant.delete()

    for file in files:
        await file.delete()


if __name__ == '__main__':
    asyncio.run(main())
