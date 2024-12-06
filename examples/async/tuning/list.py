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

    async for dataset in sdk.datasets.list(status="READY"):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.completions.from_path_deferred(
            path=local_path('example_dataset'),
            upload_format='jsonlines',
            name='foo',
        )

        operation = await dataset_draft.upload()
        dataset = await operation
        print(f'created new dataset {dataset=}')

    return dataset, dataset


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    train_dataset, validation_dataset = await get_datasets(sdk)
    base_model = sdk.models.completions('yandexgpt-lite')

    task_ids = set()
    for _ in range(1):
        tuning_task = await base_model.tune_deferred(
            train_dataset,
            validation_datasets=validation_dataset,
            name=str(uuid.uuid4())
        )
        task_ids.add(tuning_task.id)

    # NB: tuning tasks have a time gap, before they will
    # be available at the backend as a `TuningTasks`
    await asyncio.sleep(5)

    async for tuning_task in sdk.tuning.list():
        # or you could wait for tasks, instead of canceling
        print(f'found task {tuning_task=}, canceling')
        await tuning_task.cancel()


if __name__ == '__main__':
    asyncio.run(main())
