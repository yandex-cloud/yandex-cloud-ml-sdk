import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

import httpx
import pytest
from pytest_httpx import HTTPXMock

from yandex_cloud_ml_sdk._datasets.dataset import AsyncDataset, Dataset
from yandex_cloud_ml_sdk._types.misc import UNDEFINED


@pytest.fixture
def mock_dataset(mocker):
    """Create a mock dataset for testing."""
    dataset = mocker.MagicMock(spec=Dataset)
    dataset.id = "test-dataset-id"
    dataset.task_type = "test-task-type"
    return dataset


@pytest.fixture
def mock_async_dataset(mocker):
    """Create a mock async dataset for testing."""
    dataset = mocker.MagicMock(spec=AsyncDataset)
    dataset.id = "test-dataset-id"
    dataset.task_type = "test-task-type"
    return dataset


def test_download_to_temp_dir(httpx_mock: HTTPXMock, mock_dataset, mocker):
    """Test downloading dataset to a temporary directory."""
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"test file content"
    )
    
    # Call download method
    result = mock_dataset.download(timeout=30)
    
    # Verify the result
    assert isinstance(result, Iterable)
    paths = list(result)
    assert len(paths) == 1
    assert paths[0].name == "file1.txt"
    assert paths[0].read_bytes() == b"test file content"
    
    # Verify temp directory was created
    temp_dir = Path(tempfile.gettempdir()) / "ycml" / "datasets" / mock_dataset.id
    assert temp_dir.exists()
    
    # Clean up
    shutil.rmtree(temp_dir)


def test_download_to_custom_dir(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test downloading dataset to a custom directory."""
    # Create empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"test file content"
    )
    
    # Call download method with custom path
    result = mock_dataset.download(download_path=empty_dir, timeout=30)
    
    # Verify the result
    paths = list(result)
    assert len(paths) == 1
    assert paths[0] == empty_dir / "file1.txt"
    assert paths[0].read_bytes() == b"test file content"


def test_download_multiple_files(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
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
    result = mock_dataset.download(download_path=empty_dir, timeout=30)
    
    # Verify the result
    paths = list(result)
    assert len(paths) == 2
    assert {p.name for p in paths} == {"file1.txt", "file2.txt"}
    assert (empty_dir / "file1.txt").read_bytes() == b"content of file 1"
    assert (empty_dir / "file2.txt").read_bytes() == b"content of file 2"


def test_download_to_non_existent_dir(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test downloading to a non-existent directory raises an error."""
    non_existent_dir = tmp_path / "does_not_exist"
    
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Call download method with non-existent path
    with pytest.raises(ValueError, match="does not exist"):
        mock_dataset.download(download_path=non_existent_dir, timeout=30)


def test_download_to_file_path(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
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
        mock_dataset.download(download_path=file_path, timeout=30)


def test_download_to_non_empty_dir(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test downloading to a non-empty directory raises an error."""
    # Create non-empty directory
    non_empty_dir = tmp_path / "non_empty"
    non_empty_dir.mkdir()
    (non_empty_dir / "existing_file.txt").write_text("existing content")
    
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Call download method with non-empty directory
    with pytest.raises(ValueError, match="is not empty"):
        mock_dataset.download(download_path=non_empty_dir, timeout=30)


def test_download_http_error(httpx_mock: HTTPXMock, mock_dataset, tmp_path, mocker):
    """Test handling HTTP errors during download."""
    # Create empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
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
        mock_dataset.download(download_path=empty_dir, timeout=30)


@pytest.mark.asyncio
async def test_async_download(httpx_mock: HTTPXMock, mock_async_dataset, tmp_path, mocker):
    """Test async downloading of dataset."""
    # Create empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_async_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"async test content"
    )
    
    # Call async download method
    result = await mock_async_dataset.download(download_path=empty_dir, timeout=30)
    
    # Verify the result
    paths = list(result)
    assert len(paths) == 1
    assert paths[0] == empty_dir / "file1.txt"
    assert paths[0].read_bytes() == b"async test content"


def test_download_with_undefined_path(httpx_mock: HTTPXMock, mock_dataset, mocker):
    """Test downloading with UNDEFINED path uses temp directory."""
    # Mock the _get_download_urls method
    mocker.patch.object(
        mock_dataset, "_get_download_urls", 
        return_value=[("file1.txt", "https://example.com/file1.txt")]
    )
    
    # Mock the HTTP response
    httpx_mock.add_response(
        url="https://example.com/file1.txt",
        content=b"test content"
    )
    
    # Call download method with UNDEFINED path
    result = mock_dataset.download(download_path=UNDEFINED, timeout=30)
    
    # Verify the result
    paths = list(result)
    assert len(paths) == 1
    assert paths[0].name == "file1.txt"
    assert paths[0].read_bytes() == b"test content"
    
    # Clean up
    temp_dir = Path(tempfile.gettempdir()) / "ycml" / "datasets" / mock_dataset.id
    shutil.rmtree(temp_dir)
