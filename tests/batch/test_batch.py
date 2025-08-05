from __future__ import annotations

import pathlib
import uuid

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML

pytestmark = pytest.mark.asyncio


@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_batch_list(async_sdk: AsyncYCloudML, completions_jsonlines: pathlib.Path) -> None:
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

    task_id = operation.id

    operation2 = await async_sdk.batch.get(task_id)
    assert operation is not operation2

    async for operation in async_sdk.batch.list_operations():
        if operation.id == task_id:
            break
    else:
        assert False, "operation not found"

    await operation

    await operation.delete()
