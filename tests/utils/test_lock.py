# pylint: disable=unused-argument,arguments-differ,protected-access,unnecessary-lambda-assignment
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from typing_extensions import override

from yandex_cloud_ml_sdk._auth import RefresheableIAMTokenAuth
from yandex_cloud_ml_sdk._testing.client import MockClient
from yandex_cloud_ml_sdk._utils.contextlib import nullcontext
from yandex_cloud_ml_sdk._utils.sync import run_sync


class RefresheableMockAuth(RefresheableIAMTokenAuth):
    def __init__(self, sleep_time: float):
        super().__init__(None)
        self.sleep_time = sleep_time
        self.call_counter = 0

    @override
    async def _get_token(self, *args: Any, **kwargs: Any) -> str:  # type: ignore[override]
        self.call_counter += 1
        await asyncio.sleep(self.sleep_time)

        return '<mock-token>'

    async def applicable_from_env(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        return None


@pytest.mark.asyncio
async def test_auth_no_lock(folder_id, async_sdk):
    auth = RefresheableMockAuth(1)

    # using str port value for exception raising in case of network usage
    client = MockClient(port='<intencionally-non-int-value>', auth=auth, sdk=async_sdk)
    client._auth_lock._inst = nullcontext()

    coros = []
    for _ in range(100):
        coro = client._get_metadata(auth_required=True, timeout=60)
        coros.append(coro)

    await asyncio.gather(*coros)

    assert auth.call_counter > 1


@pytest.mark.asyncio
async def test_auth_with_lock(folder_id, async_sdk):
    auth = RefresheableMockAuth(1)

    # using str port value for exception raising in case of network usage
    client = MockClient(port='<intencionally-non-int-value>', auth=auth, sdk=async_sdk)

    coros = []
    for _ in range(100):
        coro = client._get_metadata(auth_required=True, timeout=60)
        coros.append(coro)

    await asyncio.gather(*coros)

    assert auth.call_counter == 1


class MockSyncClient(MockClient):
    _get_metadata = run_sync(MockClient._get_metadata)  # type: ignore[arg-type,assignment]


def test_sync_auth_no_lock(folder_id, sdk):
    auth = RefresheableMockAuth(1)

    # using str port value for exception raising in case of network usage
    client = MockSyncClient(port='<intencionally-non-int-value>', auth=auth, sdk=sdk)
    client._auth_lock._inst = nullcontext()
    run = lambda _: client._get_metadata(auth_required=True, timeout=60)

    pool = ThreadPoolExecutor(100)
    list(pool.map(run, range(100)))

    assert auth.call_counter > 1


def test_sync_auth_with_lock(folder_id, sdk):
    auth = RefresheableMockAuth(1)

    # using str port value for exception raising in case of network usage
    client = MockSyncClient(port='<intencionally-non-int-value>', auth=auth, sdk=sdk)
    run = lambda _: client._get_metadata(auth_required=True, timeout=60)

    pool = ThreadPoolExecutor(100)
    list(pool.map(run, range(100)))

    assert auth.call_counter == 1
