from __future__ import annotations

import pathlib

import pytest


@pytest.fixture(name='completions_jsonlines')
def fixture_completions_jsonlines() -> pathlib.Path:
    path = pathlib.Path(__file__).parent / 'completions.jsonlines'
    assert path.is_file()
    return path
