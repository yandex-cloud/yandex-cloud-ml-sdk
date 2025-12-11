from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk._exceptions import AioRpcError

pytestmark = [pytest.mark.asyncio, pytest.mark.vcr]

async def _upload_embeddings_dataset(client, path: str, name: str):

    dataset_function = client.datasets.text_embeddings_pair if name == "pair" else client.datasets.text_embeddings_triplet

    dataset_draft = dataset_function.draft_from_path(
        path=path,
        upload_format='jsonlines',
        name=name,
    )
    return await dataset_draft.upload()


@pytest.mark.parametrize("embeddings_tune_type", ["pair", "triplet"])
@pytest.mark.allow_grpc
async def test_tuning_embeddings(async_sdk, embeddings_tune_type):
    client = async_sdk
    model = client.models.text_embeddings("text-embeddings")

    dataset = await _upload_embeddings_dataset(
        client,
        path=f'tests/tuning/tuning_data/embeddings_{embeddings_tune_type}.jsonlines',
        name=embeddings_tune_type
    )

    new_model = await model.tune(
        dataset,
        validation_datasets=dataset,
        embeddings_tune_type=embeddings_tune_type,
        name='test'
    )
    assert new_model.uri is not None
    tuned_uri = new_model.uri
    model = client.models.text_embeddings(tuned_uri)
    result = await model.run("hi")
    assert result.embedding is not None


@pytest.mark.parametrize("embeddings_tune_type", ["pair", "triplet"])
@pytest.mark.allow_grpc
async def test_tuning_embeddings_with_dimensions(async_sdk, embeddings_tune_type):
    client = async_sdk
    model = client.models.text_embeddings("text-embeddings")

    dataset = await _upload_embeddings_dataset(
        client,
        path=f'tests/tuning/tuning_data/embeddings_{embeddings_tune_type}.jsonlines',
        name=embeddings_tune_type
    )

    new_model = await model.tune(
        dataset,
        validation_datasets=dataset,
        embeddings_tune_type=embeddings_tune_type,
        name='test',
        dimensions=[35, 128],
    )
    tuned_uri = new_model.uri
    model = client.models.text_embeddings(tuned_uri)

    result = await model.run("hi")
    assert len(result.embedding) == 128

    result = await model.run("hi", dimensions=35)
    assert len(result.embedding) == 35

    with pytest.raises(AioRpcError) as excinfo:
        await model.run("hi", dimensions=40)
