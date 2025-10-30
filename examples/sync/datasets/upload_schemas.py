#!/usr/bin/env python3

from __future__ import annotations

import pprint

from yandex_cloud_ml_sdk import YCloudML


def main() -> None:
    # You can set authentication using environment variables instead of the 'auth' argument:
    # YC_OAUTH_TOKEN, YC_TOKEN, YC_IAM_TOKEN, or YC_API_KEY
    # You can also set 'folder_id' using the YC_FOLDER_ID environment variable
    sdk = YCloudML(
        #folder_id="<YC_FOLDER_ID>",
        #auth="<YC_API_KEY/YC_IAM_TOKEN>",
    )
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
