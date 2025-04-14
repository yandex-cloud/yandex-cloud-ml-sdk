from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML

pytestmark = [pytest.mark.asyncio, pytest.mark.require_env('pyarrow')]

@pytest.mark.allow_grpc
@pytest.mark.vcr
async def test_simple_read(async_sdk: AsyncYCloudML, completions_jsonlines: Path) -> None:
    name = uuid.uuid4()
    dataset_draft = async_sdk.datasets.completions.draft_from_path(
        completions_jsonlines,
        name=str(name),
        upload_format='jsonlines',
    )

    dataset = await dataset_draft.upload()

    data = [line async for line in dataset.read()]
    assert len(data) == 3
    line = data[0]
    assert isinstance(line, dict)
    assert 'request' in line
    assert 'response' in line

    await dataset.delete()
