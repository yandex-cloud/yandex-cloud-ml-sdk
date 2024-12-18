#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib
import pprint

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    HybridSearchIndexType, ReciprocalRankFusionIndexCombinationStrategy, StaticIndexChunkingStrategy,
    TextSearchIndexType, VectorSearchIndexType
)


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

    # How to create search index with all default settings:
    operation = await sdk.search_indexes.create_deferred(
        files,
        index_type=HybridSearchIndexType()
    )
    default_search_index = await operation.wait()
    print("new hybrid search index with default settings:")
    pprint.pprint(default_search_index)

    # But you could override any default:
    operation = await sdk.search_indexes.create_deferred(
        files,
        index_type=HybridSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=700,
                chunk_overlap_tokens=300
            ),
            # you could also override some text/vector indexes settings
            text_search_index=TextSearchIndexType(),
            vector_search_index=VectorSearchIndexType(),
            normalization_strategy='L2',
            # you don't really want to change `k` parameter if you don't
            # really know what you are doing
            combination_strategy=ReciprocalRankFusionIndexCombinationStrategy(
                k=60
            )
        )
    )
    search_index = await operation.wait()
    print("new hybrid search index with overridden settings:")
    pprint.pprint(search_index)

    # And how to use your index you could learn in example file "assistant_with_search_index.py".
    # Working with hybrid index does not differ from working with any other index besides creation.

    # Created resources cleanup:
    for file in files:
        await file.delete()

    for search_index in [default_search_index, search_index]:
        print(f"delete {search_index.id=}")
        await search_index.delete()


if __name__ == '__main__':
    asyncio.run(main())
