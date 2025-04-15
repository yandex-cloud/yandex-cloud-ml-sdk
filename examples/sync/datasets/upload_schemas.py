#!/usr/bin/env python3

from __future__ import annotations

import pprint

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    sdk = YCloudML(folder_id='b1ghsjum2v37c2un8h64')
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
        schemas = sdk.datasets.list_upload_schemas(task_type)
        print(f'Schemas for {task_type=}:')
        pprint.pprint([schema.json for schema in schemas])


if __name__ == '__main__':
    main()
