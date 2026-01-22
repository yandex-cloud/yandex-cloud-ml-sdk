#!/usr/bin/env python3

from __future__ import annotations

import os
import pathlib
import tempfile

from yandex_ai_studio_sdk import YCloudML

MULT_FACTOR = 15000


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

    # We will create a "large" temporary file for illustrative purposes only.
    small_dataset = local_path('completions.jsonlines').read_bytes()
    assert len(small_dataset.splitlines()) == 3
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp:
        for _ in range(MULT_FACTOR):
            tmp.write(small_dataset)

        size_mb = tmp.tell() / 1024 ** 2
        path = tmp.name

    print(f"created temporary file {path} with filesize={size_mb:.2f}MB")
    try:
        dataset_draft = sdk.datasets.draft_from_path(
            task_type='TextToTextGeneration',
            path=path,
            upload_format='jsonlines',
            name='big_dataset',
        )

        # We are passing chunk_size parameter with a value of 5 MB (it is the minimum possible);
        # because the chunk size is smaller than the file size, the multipart upload mechanism will be used.
        # The parallelism parameter shows how many chunks will be uploaded at the same time.
        # It is recommended to choose the chunk_size and parallelism values based on
        # the available memory size and network capacity.
        dataset = dataset_draft.upload(
            chunk_size=5 * 1024 ** 2,
            parallelism=3
        )
    finally:
        os.unlink(path)

    print(f'new {dataset=}')

    for dataset in sdk.datasets.list(name_pattern='big_dataset'):
        dataset.delete()


if __name__ == '__main__':
    main()
