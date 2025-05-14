from __future__ import annotations

import pathlib
from typing import Iterator

import pytest


@pytest.fixture(name='test_file_path')
def fixture_test_file_path(tmp_path) -> Iterator[pathlib.Path]:
    path = tmp_path / 'test_file'
    path.write_bytes(b'secret number is 997')
    yield path
