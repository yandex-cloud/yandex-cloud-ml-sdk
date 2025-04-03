# pylint: disable=no-name-in-module
# pylint: disable=redefined-outer-name
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo

from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset


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


@pytest.mark.asyncio
async def test_download_to_temp_dir(mock_dataset, httpx_mock: HTTPXMock, mocker, tmp_path: Path) -> None:
    """Test downloading dataset to a temporary directory."""
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"test file content"
    )

    paths = await mock_dataset.download(timeout=30, download_path=tmp_path)

    assert paths == (tmp_path / "file1.txt", )
    assert paths[0].read_bytes() == b"test file content"


@pytest.mark.asyncio
async def test_download_multiple_files(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test downloading multiple files from a dataset."""
    # Create empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[
            ("file1.txt", "https://example.com/file1.txt"),
            ("file2.txt", "https://example.com/file2.txt"),
        ]
    )

    # Mock the HTTP responses
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"content of file 1"
    )
    httpx_mock.add_response(
        url="https://example.com/file2.txt",
        content=b"content of file 2"
    )

    # Call download method
    result = await mock_dataset.download(download_path=empty_dir, timeout=30)

    # Verify the result
    paths = list(result)
    assert len(paths) == 2
    assert {p.name for p in paths} == {"file1.txt", "file2.txt"}
    assert (empty_dir / "file1.txt").read_bytes() == b"content of file 1"
    assert (empty_dir / "file2.txt").read_bytes() == b"content of file 2"


@pytest.mark.asyncio
async def test_download_to_non_existent_dir(mock_dataset, tmp_path, mocker):
    """Test downloading to a non-existent directory raises an error."""
    non_existent_dir = tmp_path / "does_not_exist"

    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Call download method with non-existent path
    with pytest.raises(ValueError, match="does not exist"):
        await mock_dataset.download(download_path=non_existent_dir, timeout=30)


@pytest.mark.asyncio
async def test_download_to_file_path(mock_dataset, tmp_path, mocker):
    """Test downloading to a file path raises an error."""
    # Create the file
    file_path = tmp_path / "file.txt"
    file_path.touch()

    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Call download method with file path
    with pytest.raises(ValueError, match="is not a directory"):
        await mock_dataset.download(download_path=file_path, timeout=30)


@pytest.mark.asyncio
async def test_download_to_non_empty_dir(mock_dataset, tmp_path, mocker):
    """Test downloading to a non-empty directory raises an error."""
    # Create non-empty directory
    non_empty_dir = tmp_path / "non_empty"
    non_empty_dir.mkdir()
    (non_empty_dir / "file1.txt").write_text("existing content")

    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Call download method with non-empty directory
    with pytest.raises(ValueError, match="already exists"):
        await mock_dataset.download(download_path=non_empty_dir, timeout=30)


@pytest.mark.asyncio
async def test_download_http_error(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test handling HTTP errors during download."""

    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Mock HTTP error response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        status_code=404
    )

    # Call download method
    with pytest.raises(httpx.HTTPStatusError):
        await mock_dataset.download(download_path=tmp_path, timeout=30)


@pytest.mark.asyncio
async def test_download_with_exist_ok(mock_dataset, httpx_mock: HTTPXMock, mocker, tmp_path: Path) -> None:
    non_empty_dir = tmp_path / "non_empty"
    non_empty_dir.mkdir()
    (non_empty_dir / "file1.txt").write_text("existing content")

    mocker.patch.object(
        mock_dataset, "_get_download_urls",
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )

    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"test file content"
    )

    paths = await mock_dataset.download(timeout=30, download_path=tmp_path, exist_ok=False)

    assert paths == (tmp_path / "file1.txt", )
    assert paths[0].read_bytes() == b"test file content"
