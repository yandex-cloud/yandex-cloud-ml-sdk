#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import uuid

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.tuning import optimizers as to
from yandex_cloud_ml_sdk.tuning import schedulers as ts
from yandex_cloud_ml_sdk.tuning import types as tt


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
        name=str(uuid.uuid4()),
        description="cool tuning",
        labels={'good': 'yes'},
        seed=500,
        lr=1e-4,
        n_samples=100,
        tuning_type=tt.TuningTypePromptTune(virtual_tokens=20),
        scheduler=ts.SchedulerLinear(
            warmup_ratio=0.1,
            min_lr=0
        ),
        optimizer=to.OptimizerAdamw(
            beta1=0.9,
            beta2=0.999,
            eps=1e-8,
            weight_decay=0.1,
        )
    )
    print(f'new {tuning_task=}')

    try:
        new_model = tuning_task.wait()
        print(f'tuning result: {new_model}')
        print(f'new model url: {new_model.uri}')
    except BaseException:
        tuning_task.cancel()
        raise


if __name__ == '__main__':
    main()
