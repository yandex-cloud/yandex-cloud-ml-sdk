# pylint: disable=no-name-in-module
# pylint: disable=redefined-outer-name
from __future__ import annotations

import io
import uuid
from pathlib import Path

import httpx
import psutil
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pytest_httpx import HTTPXMock
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset

pytestmark = [pytest.mark.asyncio, pytest.mark.require_env('pyarrow')]


@pytest.fixture
def mock_dataset(mocker) -> AsyncDataset:
    """Create a mock dataset for testing."""
    sdk_mock = mocker.MagicMock()
    sdk_mock._client.httpx.return_value = httpx.AsyncClient()

    dataset = AsyncDataset._from_proto(
        sdk=sdk_mock,
        proto=DatasetInfo(
            dataset_id="id"
        )
    )

    return dataset



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

    process = psutil.Process()
    fd_num = process.num_fds()
    data = [line async for line in dataset.read()]

    assert process.num_fds() == fd_num

    assert len(data) == 3
    line = data[0]
    assert isinstance(line, dict)
    assert 'request' in line
    assert 'response' in line

    await dataset.delete()

def make_parquet_bytes(name: str) -> bytes:
    table = pa.table({"name": [name]})
    sink = io.BytesIO()
    pq.write_table(table, sink)
    return sink.getvalue()

@pytest.mark.asyncio
async def test_reading_order(mock_dataset, httpx_mock: HTTPXMock, mocker, tmp_path: Path) -> None:
    """Test checks files reading order """
    non_empty_dir = tmp_path / "non_empty"
    non_empty_dir.mkdir()

    file_names = ["1.parquet", "3.parquet", "test.parquet", "4.parquet", "2.parquet"]

    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[
            (non_empty_dir / fname, f"https://example.com/{fname}") for fname in file_names
        ]
    )
    for fname in file_names:
        httpx_mock.add_response(
            url=f"https://example.com/{fname}",
            content=make_parquet_bytes(fname)
        )

    process = psutil.Process()
    fd_num = process.num_fds()

    data = [line async for line in mock_dataset.read()]

    assert process.num_fds() == fd_num
    assert data == [{'name': '1.parquet'},
                    {'name': '2.parquet'},
                    {'name': '3.parquet'},
                    {'name': '4.parquet'},
                    {'name': 'test.parquet'}]
