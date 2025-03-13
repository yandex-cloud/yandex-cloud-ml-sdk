#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import uuid

from yandex_cloud_ml_sdk import YCloudML


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def get_datasets(sdk, name, dataset_function):
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

    for dataset in sdk.datasets.list(status='READY', name_pattern=name):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = dataset_function.draft_from_path(
            path=local_path(f'{name}.jsonlines'),
            upload_format='jsonlines',
            name=name,
        )

        dataset = dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset, dataset


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()
    base_model = sdk.models.text_embeddings('yandexgpt-lite')

    for name, tune_type, dataset_function in [
        ('embeddings_pair', 'pair', sdk.datasets.text_embeddings_pair),
        ('embeddings_triplet', 'triplet', sdk.datasets.text_embeddings_triplet),
    ]:
        train_dataset, validation_dataset = get_datasets(sdk, name, dataset_function)
        result = base_model.run("hi")
        print(f'pretrain model inference result: {result}')

        # `.tune(...)` is a shortcut for:
        # tuning_task = base_model.tune_deferred(...)
        # new_model = tuning_task.wait(...)
        # But it gives you less control on tune canceling and
        # reporting.
        new_model = base_model.tune(
            train_dataset,
            validation_datasets=validation_dataset,
            embeddings_tune_type=tune_type,
            name=str(uuid.uuid4())
        )
        print(f'resulting {new_model}')

        # you can save model.uri somewhere and reuse it later
        tuned_uri = new_model.uri
        model = sdk.models.text_embeddings(tuned_uri)
        result = model.run("hi")
        print(f'posttrain model inference result: {result}')


if __name__ == '__main__':
    main()
