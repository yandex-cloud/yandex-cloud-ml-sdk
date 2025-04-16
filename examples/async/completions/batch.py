#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def get_dataset(sdk):
    """
    This function represents getting or creating dataset object.

    In real life you could use just a datasets ids, for example:

    ```
    dataset = await sdk.datasets.get("some_id")
    tuning_task = await base_model.tune_deferred(
        "dataset_id",
        validation_datasets=dataset
    )
    ```
    """

    async for dataset in sdk.datasets.list(status='READY', name_pattern=NAME):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.draft_from_path(
            task_type='TextToTextGenerationRequest',
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name=NAME,
        )

        dataset = await dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    dataset = await get_dataset(sdk)

    model = sdk.models.completions('gemma-3-12b-it')

    operation = await model.batch.run_deferred(dataset)

    print(operation)
    result = await operation

    print(operation)
    print(result)
    async for line in result.read():
        print(line)


if __name__ == '__main__':
    asyncio.run(main())
