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
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name=NAME,
    )

    # .upload is actually wrapper around an .upload_deferred method,
    # which would be described below
    dataset = await dataset_draft.upload()
    print(f'new {dataset=}')

    # NB: `.datasets.completions` is a shortcut for `.datasets(task_type='TextToTextGeneration')`
    dataset_draft = sdk.datasets.completions.draft_from_path(local_path('completions.jsonlines'))
    # Example how you could setup dataset_draft after it's creation:
    dataset_draft.upload_format = 'jsonlines'
    dataset_draft.name = NAME
    dataset_draft.allow_data_logging = True

    # .upload_deferred is very complicated method, which not only creates dataset at the backend,
    # not only uploads data, but also lanches validation operation and returns Operation
    # object to follow
    operation = await dataset_draft.upload_deferred()
    dataset = await operation
    print(f'new {dataset=}')

    # You could call .list not only on .datasets,
    # but on .completions helper as well, it will substitute corresponding task_type as a filter
    async for dataset in sdk.datasets.completions.list(name_pattern=NAME):
        await dataset.delete()

    async for dataset in sdk.datasets.list(name_pattern=NAME):
        await dataset.delete()


if __name__ == '__main__':
    asyncio.run(main())
