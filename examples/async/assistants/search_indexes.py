#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_indexes import StaticIndexChunkingStrategy, TextSearchIndexType


async def main() -> None:
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
        service_map={
            'ai-files': 'assistant.api.cloud.yandex.net',
            'ai-assistants': 'assistant.api.cloud.yandex.net',
            'operation': 'assistant.api.cloud.yandex.net',
        }
    )

    file_coros = (
        sdk.files.upload(
            pathlib.Path(__file__).parent / path,
            ttl_days=5,
            expiration_policy="static",
        )
        for path in ['turkey_example.txt', 'maldives_example.txt']
    )
    files = await asyncio.gather(*file_coros)

    operation = await sdk.search_indexes.create_deferred(
        files,
        index_type=TextSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=700,
                chunk_overlap_tokens=300,
            )
        )
    )
    search_index = await operation.wait()
    print(f"search index {search_index}")

    for file in files:
        print(f"delete file {file}")
        await file.delete()

    async for search_index in sdk.search_indexes.list():
        print(f"delete search_index {search_index}")
        await search_index.delete()


if __name__ == '__main__':
    asyncio.run(main())
