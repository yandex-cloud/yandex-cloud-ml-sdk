#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def get_dataset(sdk):
    """
    This function represents getting or creating dataset object.

    In real life you could use just a datasets ids, for example:

    ```
    dataset = sdk.datasets.get("some_id")

    batch_task = model.batch.run_deferred(dataset)
    # or just
    batch_task = model.batch.run_deferred("dataset_id")
    ```

    To get to know better how to work with datasets,
    please refer to special "datasets/" examples.
    """

    for dataset in sdk.datasets.list(status='READY', name_pattern=NAME):
        print(f'using old dataset {dataset=}')
        break
    else:
        print('no old datasets found, creating new one')
        dataset_draft = sdk.datasets.draft_from_path(
            task_type='TextToTextGenerationRequest',
            path=local_path('completions.jsonlines'),
            upload_format='jsonlines',
            name=NAME,
        )

        dataset = dataset_draft.upload()
        print(f'created new dataset {dataset=}')

    return dataset


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    # This is "usual" dataset as for tuning, but it have
    # to have proper "task_type" to work with batch runs
    dataset = get_dataset(sdk)

    # There are only specific models supports batch runs,
    # please refer to Yandex Foundation Models doctumentation
    model = sdk.models.completions('gemma-3-12b-it')

    # Batch run returns an operation object you could
    # follow or just call .wait method
    operation = model.batch.run_deferred(dataset)

    resulting_dataset = operation.wait()

    # NB: Resulting dataset have task_type="TextToTextGeneration" and could be used as an input
    # for tuning.

    try:
        import pyarrow  # pylint: disable=import-outside-toplevel,unused-import # noqa

        print('Resulting dataset lines:')
        for line in resulting_dataset.read():
            print(line)
    except ImportError:
        print('skipping dataset read; istall yandex-cloud-ml-sdk[datasets] to be able to read')

    # Removing final dataset to not to increase chaos.
    resulting_dataset.delete()

if __name__ == '__main__':
    main()
