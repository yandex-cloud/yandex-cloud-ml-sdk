#!/usr/bin/env python3

from __future__ import annotations

import pathlib

from yandex_cloud_ml_sdk import YCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'

def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name=NAME,
    )

    # .upload is actually wrapper around an .upload_deferred method,
    # which would be described below
    dataset = dataset_draft.upload()
    print(f'new {dataset=}')

    # NB: `.datasets.completions` is a shortcut for `.datasets(task_type='TextToTextGeneration')`
    dataset_draft = sdk.datasets.completions.draft_from_path(local_path('completions.jsonlines'))
    # Example how you could setup dataset_draft after it's creation:
    dataset_draft.upload_format = 'jsonlines'
    dataset_draft.name = NAME
    dataset_draft.allow_data_logging = True

    # .upload_deferred is very complicated method, which not only creates dataset at the backend,
    # not only uploads data, but also lanches validation operation and returns Operation
    # object to follow
    operation = dataset_draft.upload_deferred()
    dataset = operation.wait()
    print(f'new {dataset=}')

    # You could call .list not only on .datasets,
    # but on .completions helper as well, it will substitute corresponding task_type as a filter
    for dataset in sdk.datasets.completions.list(name_pattern=NAME):
        dataset.delete()

    for dataset in sdk.datasets.list(name_pattern=NAME):
        dataset.delete()


if __name__ == '__main__':
    main()
