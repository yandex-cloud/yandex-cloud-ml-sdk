# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk.auth import NoAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='auth')
def fixture_auth():
    return NoAuth()


async def test_auth(async_sdk):
    metadata = await async_sdk._client._get_metadata(
        auth_required=True,
        timeout=1
    )
    assert metadata == (('yc-ml-sdk-retry', 'NONE'),)


async def test_applicable_from_env():
    assert await NoAuth.applicable_from_env() is None
