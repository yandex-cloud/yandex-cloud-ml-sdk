#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import time
import uuid

from yandex_cloud_ml_sdk import YCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def get_datasets(sdk):
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

    for dataset in sdk.datasets.list(status='READY', name_pattern='completions'):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.completions.from_path_deferred(
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name='completions',
        )

        operation = dataset_draft.upload()
        dataset = operation.wait()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    train_dataset, validation_dataset = get_datasets(sdk)
    base_model = sdk.models.completions('yandexgpt-lite')

    tuning_task = base_model.tune_deferred(
        train_dataset,
        validation_datasets=validation_dataset,
        name=str(uuid.uuid4())
    )
    print(f'new {tuning_task=}')

    try:
        same_task = base_model.attach_tune_deferred(tuning_task.id)
        print(f'{same_task=}')

        # IMPORTANT
        # .get will raise NOT_FOUND first few seconds, before Yandex Cloud "Operation"
        # will create a "TuningTask" at the backend.
        time.sleep(5)

        same_task2 = sdk.tuning.get(tuning_task.id)
        print(f'{same_task2=}')
    finally:
        tuning_task.cancel()


if __name__ == '__main__':
    main()
