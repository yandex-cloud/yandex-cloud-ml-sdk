#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import threading
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

    tuning_task = base_model.tune_deferred(
        train_dataset,
        validation_datasets=validation_dataset,
        name=str(uuid.uuid4())
    )
    print(f'new {tuning_task=}')

    report_stop = threading.Event()

    def report_status():
        while not report_stop.is_set():
            print('===REPORTING:')
            print(f'{tuning_task.get_status()=}')
            print(f'{tuning_task.get_task_info()=}')
            print(f'{tuning_task.get_metrics_url()=}')
            print()
            time.sleep(5)

    report_thread = threading.Thread(target=report_status)
    report_thread.start()

    try:
        new_model = tuning_task.wait()
        print(f'tuning result: {new_model}')
        print(f'new model url: {new_model.uri}')
    except BaseException:
        print('canceling task for a greater cleanup')
        tuning_task.cancel()
        raise
    finally:
        report_stop.set()
        report_thread.join()


if __name__ == '__main__':
    main()
