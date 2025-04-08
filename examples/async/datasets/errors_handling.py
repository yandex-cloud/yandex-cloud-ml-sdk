#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    dataset_draft = sdk.datasets.completions.draft_from_path(
        local_path('example_bad_dataset'),
        upload_format='jsonlines',
        name=NAME,
    )

    operation = await dataset_draft.upload_deferred()

    # We deliberately pass a bad data to dataset, to show how and when it will fail
    try:
        dataset = await operation
    except DatasetValidationError as error:
        # There are some detaile in error info about what's wrong:
        print(f"dataset creation was failed with an {error=}")
        bad_dataset = await sdk.datasets.get(error.dataset_id)
        print(f"going to delete {bad_dataset=}")
        await bad_dataset.delete()

    # We reusing dataset_draft to make an another upload;
    # Note it still contains bad data
    bad_dataset = await dataset_draft.upload(raise_on_validation_failure=False)
    print(f"New {bad_dataset=} have a bad status {bad_dataset.status=}")
    await bad_dataset.delete()

    async for dataset in sdk.datasets.list(name_pattern=NAME):
        await dataset.delete()


if __name__ == '__main__':
    asyncio.run(main())
