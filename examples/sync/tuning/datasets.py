#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    sdk = YCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
    )

    dataset_draft = sdk.datasets.from_path_deferred(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name='completions',
    )

    operation = dataset_draft.upload()
    dataset = operation.wait()
    print(f'new {dataset=}')

    dataset_draft = sdk.datasets.completions.from_path_deferred(
        local_path('example_bad_dataset')
    )
    dataset_draft.upload_format = 'jsonlines'
    dataset_draft.name = 'foo'

    operation = dataset_draft.upload()
    try:
        dataset = operation.wait()
    except DatasetValidationError as error:
        print(f"dataset creation was failed with an {error=}")
        bad_dataset = sdk.datasets.get(error.dataset_id)
        print(f"going to delete {bad_dataset=}")
        bad_dataset.delete()

    operation = dataset_draft.upload(raise_on_validation_failure=False)
    bad_dataset = operation.wait()
    print(f"New {bad_dataset=} have a bad status {dataset.status=}")
    dataset.delete()

    for dataset in sdk.datasets.list():
        dataset.delete()


if __name__ == '__main__':
    main()
