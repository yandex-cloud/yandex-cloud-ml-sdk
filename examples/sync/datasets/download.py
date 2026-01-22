#!/usr/bin/env python3

from __future__ import annotations

import pathlib
from tempfile import TemporaryDirectory

from yandex_ai_studio_sdk import YCloudML

PATH = pathlib.Path(__file__)
NAME = f'example-{PATH.parent.name}-{PATH.name}'


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


def main() -> None:
    # Because it is optional requirenment for a yandex-ai-studio-sdk, we import it inside
    import pyarrow.parquet as pq  # pylint: disable=import-outside-toplevel

    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        # folder_id="<YC_FOLDER_ID>",
        # auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
    sdk.setup_default_logging()

    # On how to upload and work with dataset drafts refer to upload.py example file
    dataset_draft = sdk.datasets.draft_from_path(
        task_type='TextToTextGeneration',
        path=local_path('completions.jsonlines'),
        upload_format='jsonlines',
        name=NAME,
    )
    dataset = dataset_draft.upload()
    print(f'new {dataset=}')

    # We use temporary directory to not to left garbage after an example run
    with TemporaryDirectory() as tmp:
        # You don't need anything to download dataset
        paths = dataset.download(download_path=tmp)
        print(f'dataset downloaded into {paths=}')

        # But you need pyarrow, or any other parquet engine to parse it
        dataset_tables = [
            pq.read_table(path) for path in paths
        ]

        for table in dataset_tables:
            print('Dataset table:')
            for line in table.to_pylist():
                print(line)

    for dataset in sdk.datasets.list(name_pattern=NAME):
        dataset.delete()


if __name__ == '__main__':
    main()
