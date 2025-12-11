from __future__ import annotations

import pytest

from src.yandex_cloud_ml_sdk import AsyncYCloudML, YCloudML
from yandex_cloud_ml_sdk._models.text_embeddings.result import TextEmbeddingsModelResult

pytestmark = [pytest.mark.asyncio, pytest.mark.vcr]

def test_tuning_pairs(sdk):
    client = sdk
    model = client.models.text_embeddings("text-embeddings")
    path = 'tuning/tuning_data/embeddings_pair.jsonlines'
    name = 'embeddings_pair'

    dataset_draft = client.datasets.text_embeddings_pair.draft_from_path(
            path=path,
            upload_format='jsonlines',
            name=name,
        )

    dataset = dataset_draft.upload()

    new_model = model.tune(
        dataset,
        validation_datasets=dataset,
        embeddings_tune_type = 'pair',
        name = 'test',
        dimensions = [35, 512]
    )
    tuned_uri = new_model.uri
    print(f'resulting {tuned_uri}')
