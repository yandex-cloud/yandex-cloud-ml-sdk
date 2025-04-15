#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import pprint

from yandex_cloud_ml_sdk import AsyncYCloudML


async def main() -> None:
    sdk = AsyncYCloudML(folder_id='b1ghsjum2v37c2un8h64')
    sdk.setup_default_logging()

    for task_type in (
        'TextToTextGeneration',
        'TextToTextGenerationRequest',
        'ImageTextToTextGenerationRequest',
        'TextEmbeddingsPair',
        'TextEmbeddingsTriplet',
        'TextClassificationMultilabel',
        'TextClassificationMulticlass',
    ):
        schemas = await sdk.datasets.list_upload_schemas(task_type)
        print(f'Schemas for {task_type=}:')
        pprint.pprint([schema.json for schema in schemas])


if __name__ == '__main__':
    asyncio.run(main())
