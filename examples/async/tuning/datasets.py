#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')

    # dataset couid be created through "helper" like .completion,
    # which is defines task_type for dataset
    upload_formats = await sdk.datasets.completions.list_upload_formats()
    print(f'available {upload_formats=} for {sdk.datasets.completions}')
    print(f'{sdk.datasets.completions.task_type=}')

    dataset = await sdk.datasets.completions.create(
        upload_format="jsonlines",
        name="MyCoolDataset",
    )
    print(f'freshly created {dataset=}')

    # or it could be created without helper
    task_type = "TextClassificationMultilabel"
    upload_formats = await sdk.datasets.list_upload_formats(task_type)
    print(f'available {upload_formats=} for {task_type=}')

    another_dataset = await sdk.datasets.create(
        task_type=task_type,
        upload_format="jsonlines",
        name="AnotherCoolDataset",
    )

    # you could also ask dataset itself about its supported formats
    upload_formats = await another_dataset.list_upload_formats()
    print(f'upload_formats {upload_formats=}')

    # also you could change some fields after dataset creation
    await dataset.update(name="NotSoCoolDataset", description="Something about dataset")
    print(f'updated {dataset=}')

    await dataset._upload_path(local_path("example_dataset"))

    # here I want to show you .list() and .delete(), I hope it speaks for itself
    async for dataset in sdk.datasets.list():
        print(f'deleting {dataset=}')
        await dataset.delete()



if __name__ == '__main__':
    asyncio.run(main())
