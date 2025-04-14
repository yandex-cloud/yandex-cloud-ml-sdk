from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def completions_jsonlines() -> pathlib.Path:
    path = pathlib.Path(__file__).parent / 'completions.jsonlines'
    assert path.is_file()
    return path
