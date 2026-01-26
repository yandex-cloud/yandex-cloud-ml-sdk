# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk.auth import APIKeyAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='api_key')
def fixture_api_key():
    return '<api_key>'


@pytest.fixture(name='auth')
def fixture_auth(api_key):
    return APIKeyAuth(api_key)


async def test_auth(async_sdk, api_key, get_auth_meta):
    metadata = await async_sdk._client._get_metadata(
        auth_required=True,
        timeout=1
    )
    assert get_auth_meta(metadata) == f'Api-Key {api_key}'


async def test_applicable_from_env(api_key, monkeypatch):
    monkeypatch.delenv(APIKeyAuth.env_var, raising=False)
    assert await APIKeyAuth.applicable_from_env() is None

    monkeypatch.setenv(APIKeyAuth.env_var, api_key)
    auth = await APIKeyAuth.applicable_from_env()
    assert auth
    assert auth._api_key == api_key
