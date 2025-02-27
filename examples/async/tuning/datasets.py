#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name='completions',
    )

    dataset = await dataset_draft.upload()
    print(f'new {dataset=}')

    dataset_draft = sdk.datasets.completions.draft_from_path(
        local_path('example_bad_dataset')
    )
    dataset_draft.upload_format = 'jsonlines'
    dataset_draft.name = 'foo'
    dataset_draft.allow_data_logging = True

    operation = await dataset_draft.upload_deferred()
    try:
        dataset = await operation
    except DatasetValidationError as error:
        print(f"dataset creation was failed with an {error=}")
        bad_dataset = await sdk.datasets.get(error.dataset_id)
        print(f"going to delete {bad_dataset=}")
        await bad_dataset.delete()

    operation = await dataset_draft.upload_deferred(raise_on_validation_failure=False)
    bad_dataset = await operation
    print(f"New {bad_dataset=} have a bad status {bad_dataset.status=}")
    await dataset.delete()

    # You could call .list not only on .datasets,
    # but on .completions helper as well, it will substitute corresponding task_type as a filter
    async for dataset in sdk.datasets.completions.list():
        await dataset.delete()

    async for dataset in sdk.datasets.list():
        await dataset.delete()


if __name__ == '__main__':
    asyncio.run(main())
