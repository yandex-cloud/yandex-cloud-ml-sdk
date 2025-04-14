#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    # This example needs to have pyarrow installed
    import pyarrow  # pylint: disable=import-outside-toplevel,unused-import # noqa

    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # On how to upload and work with dataset drafts refer to upload.py example file
    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name=NAME,
    )
    dataset = await dataset_draft.upload()
    print(f'Going to read {dataset=} records')
    async for record in dataset.read():
        print(record)

    async for dataset in sdk.datasets.list(name_pattern=NAME):
        await dataset.delete()


if __name__ == '__main__':
    asyncio.run(main())
