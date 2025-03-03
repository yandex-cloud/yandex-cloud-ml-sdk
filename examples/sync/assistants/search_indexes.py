#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_indexes import StaticIndexChunkingStrategy, TextSearchIndexType


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    files = []
    for path in ['turkey_example.txt', 'maldives_example.txt']:
        file = sdk.files.upload(
            local_path(path),
            ttl_days=5,
            expiration_policy="static",
        )
        files.append(file)

    operation = sdk.search_indexes.create_deferred(
        [files[0]],
        index_type=TextSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=700,
                chunk_overlap_tokens=300,
            )
        )
    )
    search_index = operation.wait()
    print(f"new {search_index=}")

    search_index2 = sdk.search_indexes.get(search_index.id)
    print(f"same as first, {search_index2=}")

    search_index.update(name="foo")
    print(f"now with a name {search_index=}")

    # We could also add files to index later:
    add_operation = search_index.add_files_deferred(files[1])
    new_index_files = add_operation.wait()
    print(f"{new_index_files=}")

    index_files = [file for file in search_index.list_files()]
    print(f"search index files: {index_files}")

    index_file = search_index.get_file(index_files[0].id)
    print(f"search index file: {index_file}")

    for file in files:
        file.delete()

    for search_index in sdk.search_indexes.list():
        print(f"delete {search_index=}")
        search_index.delete()


if __name__ == '__main__':
    main()
