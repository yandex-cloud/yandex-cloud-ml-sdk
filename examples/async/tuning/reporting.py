#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib
import uuid

from yandex_ai_studio_sdk import AsyncAIStudio


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
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = AsyncAIStudio(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()
    train_dataset, validation_dataset = await get_datasets(sdk)
    base_model = sdk.models.completions('yandexgpt-lite')

    tuning_task = await base_model.tune_deferred(
        train_dataset,
        validation_datasets=validation_dataset,
        name=str(uuid.uuid4())
    )
    print(f'new {tuning_task=}')

    async def report_status():
        while True:
            print('===REPORTING:')
            print(f'{await tuning_task.get_status()=}')
            print(f'{await tuning_task.get_task_info()=}')
            print(f'{await tuning_task.get_metrics_url()=}')
            print()
            await asyncio.sleep(5)

    report_task = asyncio.create_task(report_status())

    try:
        new_model = await tuning_task
        print(f'tuning result: {new_model}')
        print(f'new model url: {new_model.uri}')
    except BaseException:
        print('canceling task for a greater cleanup')
        await tuning_task.cancel()
        raise
    finally:
        report_task.cancel()
        try:
            # we need to fetch exceptions from report_task
            await report_task
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    asyncio.run(main())
