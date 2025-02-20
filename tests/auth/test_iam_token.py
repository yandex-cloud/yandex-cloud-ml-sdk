# pylint: disable=protected-access
from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk.auth import IAMTokenAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='iam_token')
def fixture_iam_token():
    return '<iam_token>\n'


@pytest.fixture(name='auth')
def fixture_auth(iam_token):
    return IAMTokenAuth(iam_token)


async def test_auth(async_sdk, iam_token, get_auth_meta):
    metadata = await async_sdk._client._get_metadata(
        auth_required=True,
        timeout=1
    )
    assert get_auth_meta(metadata) == f'Bearer {iam_token.strip()}'


async def test_applicable_from_env(iam_token, monkeypatch):
    monkeypatch.delenv(IAMTokenAuth.env_var, raising=False)
    assert await IAMTokenAuth.applicable_from_env() is None

    monkeypatch.setenv(IAMTokenAuth.env_var, iam_token)
    auth = await IAMTokenAuth.applicable_from_env()
    assert auth
    assert auth._token == iam_token.strip()
