from __future__ import annotations

import pathlib
import sys

pytest_plugins = [
    'pytest_asyncio',
    'pytest_recording',
    'yandex_cloud_ml_sdk._testing.plugin',
]

langchain_paths = [
    'examples/langchain/',
    'tests/langchain_',
    'src/yandex_cloud_ml_sdk/_types/langchain.py',
    'src/yandex_cloud_ml_sdk/_utils/langchain.py',
    'src/yandex_cloud_ml_sdk/_models/completions/langchain.py',
]

def pytest_ignore_collect(collection_path, path, config):  # pylint: disable=unused-argument
    if sys.version_info > (3, 9):
        return None

    base_path = pathlib.Path(__file__).parent
    for suffix in langchain_paths:
        path_to_ignore = base_path / suffix
        if str(collection_path).startswith(str(path_to_ignore)):
            return True

    return None
