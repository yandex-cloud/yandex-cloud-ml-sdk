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
    dataset = sdk.datasets.get("some_id")
    tuning_task = base_model.tune_deferred(
        "dataset_id",
        validation_datasets=dataset
    )
    ```
    """

    async for dataset in sdk.datasets.list(status='READY', name_pattern='multilabel'):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.text_classifiers_multilabel.from_path_deferred(
            path=local_path('multilabel_classification.jsonlines'),
            upload_format='jsonlines',
            name='multilabel',
        )

        operation = await dataset_draft.upload()
        dataset = await operation.wait()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    train_dataset, validation_dataset = await get_datasets(sdk)
    base_model = sdk.models.text_classifiers('yandexgpt-lite')

    # `.tune(...)` is a shortcut for:
    # tuning_task = await base_model.tune_deferred(...)
    # new_model = await tuning_task.wait(...)
    # But it gives you less control on tune canceling and
    # reporting.
    new_model = await base_model.tune(
        train_dataset,
        validation_datasets=validation_dataset,
        classification_type='multilabel',
        name=str(uuid.uuid4())
    )
    print(f'resulting {new_model}')

    classification_result = await new_model.run("neutrino")
    print(f'{classification_result=}')

    # or save model.uri somewhere and reuse it later
    tuned_uri = new_model.uri
    model = sdk.models.text_classifiers(tuned_uri)

    classification_result = await model.run("improper integral")
    print(f'{classification_result=}')


if __name__ == '__main__':
    asyncio.run(main())