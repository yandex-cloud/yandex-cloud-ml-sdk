# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk.auth import EnvIAMTokenAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='iam_token')
def fixture_iam_token():
    return '<iam_token>'


@pytest.fixture(name='auth')
def fixture_auth(iam_token, monkeypatch):
    monkeypatch.setenv(EnvIAMTokenAuth.default_env_var, iam_token)
    return EnvIAMTokenAuth()


async def test_auth(async_sdk, iam_token, monkeypatch, get_auth_meta):
    metadata = await async_sdk._client._get_metadata(
        auth_required=True,
        timeout=1
    )
    assert get_auth_meta(metadata) == f'Bearer {iam_token}'

    monkeypatch.setenv(EnvIAMTokenAuth.default_env_var, 'foo')
    metadata = await async_sdk._client._get_metadata(
        auth_required=True,
        timeout=1
    )
    assert get_auth_meta(metadata) == 'Bearer foo'


async def test_applicable_from_env(iam_token, monkeypatch):
    monkeypatch.delenv(EnvIAMTokenAuth.default_env_var, raising=False)
    assert await EnvIAMTokenAuth.applicable_from_env() is None

    monkeypatch.setenv(EnvIAMTokenAuth.default_env_var, iam_token)
    auth = await EnvIAMTokenAuth.applicable_from_env()
    assert auth
    assert (
        await auth.get_auth_metadata(client=None, timeout=None, lock=None) ==
        ('authorization', f'Bearer {iam_token}')
    )
