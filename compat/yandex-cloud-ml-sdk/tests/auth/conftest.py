# pylint: disable=protected-access
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(name="mock_client")
def fixture_mock_client(monkeypatch):
    client_mock = MagicMock()
    client_mock.get = AsyncMock()

    constructor_mock = MagicMock()
    constructor_mock.return_value.__aenter__.return_value = client_mock

    monkeypatch.setattr("httpx.AsyncClient", constructor_mock)

    yield client_mock


@pytest.fixture(name="process_maker")
def fixture_process_maker():
    class MockProcess:
        def __init__(self, returncode=0, stdout=b"", stderr=b""):
            self.returncode = returncode
            self.stdout = AsyncMock()
            self.stderr = AsyncMock()

            # Мы используем AsyncMock для асинхронных методов.
            self.communicate = AsyncMock(return_value=(stdout, stderr))

        async def wait(self):
            return self.returncode

        def kill(self):
            pass

        def terminate(self):
            pass

    return MockProcess

@pytest.fixture(name="get_auth_meta")
def fixture_get_auth_meta():
    def getter(metadata):
        for key, value in metadata:
            if key == 'authorization':
                return value
        return None
    return getter
