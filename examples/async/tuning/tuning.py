#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pathlib

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.exceptions import DatasetValidationError


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


async def main() -> None:
    sdk = AsyncYCloudML(
        folder_id='b1ghsjum2v37c2un8h64',
    )

    async for dataset in sdk.datasets.list(status="READY"):
        print(f'using old dataset {dataset=}')
        break
    else:
        print(f'no old datasets found, creating new one')
        dataset_draft = sdk.datasets.completions.from_path_deferred(
            path=local_path('example_dataset'),
            upload_format='jsonlines',
            name='foo',
        )

        operation = await dataset_draft.upload()
        dataset = await operation
        print(f'creating new dataset {dataset=}')

    base_model = sdk.models.completions('yandexgpt')
    tuning_task = await base_model.tune_deferred(dataset)
    print(f'{tuning_task=}')
    new_model = await tuning_task




if __name__ == '__main__':
    asyncio.run(main())
