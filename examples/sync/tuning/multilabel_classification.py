#!/usr/bin/env python3

from __future__ import annotations

import pathlib
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

    for dataset in sdk.datasets.list(status='READY', name_pattern='multilabel'):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.text_classifiers_multilabel.draft_from_path(
            path=local_path('multilabel_classification.jsonlines'),
            upload_format='jsonlines',
            name='multilabel',
        )

        dataset = dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()
    train_dataset, validation_dataset = get_datasets(sdk)
    base_model = sdk.models.text_classifiers('yandexgpt-lite')

    # `.tune(...)` is a shortcut for:
    # tuning_task = base_model.tune_deferred(...)
    # new_model = tuning_task.wait(...)
    # But it gives you less control on tune canceling and
    # reporting.
    new_model = base_model.tune(
        train_dataset,
        validation_datasets=validation_dataset,
        classification_type='multilabel',
        name=str(uuid.uuid4())
    )
    print(f'resulting {new_model}')

    classification_result = new_model.run("neutrino")
    print(f'{classification_result=}')

    # or save model.uri somewhere and reuse it later
    tuned_uri = new_model.uri
    model = sdk.models.text_classifiers(tuned_uri)

    classification_result = model.run("improper integral")
    print(f'{classification_result=}')


if __name__ == '__main__':
    main()
