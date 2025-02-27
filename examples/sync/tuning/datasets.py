#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name='completions',
    )

    dataset = dataset_draft.upload()
    print(f'new {dataset=}')

    dataset_draft = sdk.datasets.completions.draft_from_path(
        local_path('example_bad_dataset')
    )
    dataset_draft.upload_format = 'jsonlines'
    dataset_draft.name = 'foo'
    dataset_draft.allow_data_logging = True

    operation = dataset_draft.upload_deferred()
    try:
        dataset = operation.wait()
    except DatasetValidationError as error:
        print(f"dataset creation was failed with an {error=}")
        bad_dataset = sdk.datasets.get(error.dataset_id)
        print(f"going to delete {bad_dataset=}")
        bad_dataset.delete()

    operation = dataset_draft.upload_deferred(raise_on_validation_failure=False)
    bad_dataset = operation.wait()
    print(f"New {bad_dataset=} have a bad status {dataset.status=}")
    dataset.delete()

    # You could call .list not only on .datasets,
    # but on .completions helper as well, it will substitute corresponding task_type as a filter
    for dataset in sdk.datasets.completions.list():
        dataset.delete()

    for dataset in sdk.datasets.list():
        dataset.delete()


if __name__ == '__main__':
    main()
