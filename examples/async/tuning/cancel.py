#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib
import uuid

from yandex_cloud_ml_sdk import AsyncYCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def get_datasets(sdk):
    """
    This function represents getting or creating datasets object.

    In real life you could use just a datasets ids, for example:

    ```
    dataset = await sdk.datasets.get("some_id")
    tuning_task = await base_model.tune_deferred(
        "dataset_id",
        validation_datasets=dataset
    )
    ```
    """

    async for dataset in sdk.datasets.list(status='READY', name_pattern='completions'):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.completions.draft_from_path(
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name='completions',
        )

        dataset = await dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()
    train_dataset, validation_dataset = await get_datasets(sdk)
    base_model = sdk.models.completions('yandexgpt-lite')

    tuning_task = await base_model.tune_deferred(
        train_dataset,
        validation_datasets=validation_dataset,
        name=str(uuid.uuid4())
    )
    print(f'new {tuning_task=}')

    try:
        for _ in range(3):
            status = await tuning_task.get_status()
            print(f'{status=}')

            task_info = await tuning_task.get_task_info()
            print(f'{task_info=}')

            await asyncio.sleep(5)
    finally:
        await tuning_task.cancel()

    status = await tuning_task.get_status()
    print(f'{status=} after cancel')

    task_info = await tuning_task.get_task_info()
    print(f'{task_info=} after cancel')


if __name__ == '__main__':
    asyncio.run(main())
