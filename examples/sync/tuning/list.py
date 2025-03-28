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
        dataset_draft = sdk.datasets.completions.draft_from_path(
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name='completions',
        )

        dataset = dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()
    train_dataset, validation_dataset = get_datasets(sdk)
    base_model = sdk.models.completions('yandexgpt-lite')

    task_ids = set()
    for _ in range(3):
        tuning_task = base_model.tune_deferred(
            train_dataset,
            validation_datasets=validation_dataset,
            name=str(uuid.uuid4())
        )
        print(f'created task {tuning_task.id=}')
        task_ids.add(tuning_task.id)

    # NB: tuning tasks have a time gap, before they will
    # be available at the backend as a `TuningTasks`
    time.sleep(5)

    print('And now - cancel all created tasks:')
    for tuning_task in sdk.tuning.list():
        if tuning_task.id in task_ids:
            # or you could wait for tasks, instead of canceling
            print(f'found task {tuning_task=}, canceling')
            tuning_task.cancel()


if __name__ == '__main__':
    main()
