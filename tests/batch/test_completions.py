from __future__ import annotations

import pathlib
import uuid

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='completions_jsonlines')
def fixture_completions_jsonlines() -> pathlib.Path:
    path = pathlib.Path(__file__).parent / 'completions.jsonlines'
    assert path.is_file()
    return path


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_simple_run(async_sdk: AsyncYCloudML, completions_jsonlines: pathlib.Path) -> None:
    name = uuid.uuid4()
    dataset_draft = async_sdk.datasets.draft_from_path(
        task_type="TextToTextGenerationRequest",
        path=completions_jsonlines,
        name=str(name),
        upload_format='jsonlines',
    )

    dataset = await dataset_draft.upload()

    model = async_sdk.models.completions('gemma-3-12b-it')
    operation = await model.batch.run_deferred(dataset)
    resulting_dataset = await operation

    assert resulting_dataset.task_type == 'TextToTextGeneration'
    # pretty random number
    assert resulting_dataset.size_bytes > 1024

    labels = resulting_dataset.labels

    assert labels.get('foundation_models_batch_task_id') == operation.task_id
    assert labels.get('foundation_models_source_dataset') == dataset.id

    await resulting_dataset.delete()
    await dataset.delete()
