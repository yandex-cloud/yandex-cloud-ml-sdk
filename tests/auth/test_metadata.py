# pylint: disable=protected-access
from __future__ import annotations

import time
from unittest.mock import MagicMock

import httpx
import pytest

from yandex_cloud_ml_sdk.auth import MetadataAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="iam_token")
def fixture_iam_token():
    return "<iam_token>"


@pytest.fixture(name="auth")
def fixture_auth():
    return MetadataAuth()


async def test_auth(async_sdk, iam_token, mock_client, get_auth_meta):
    response = httpx.Response(
        status_code=200,
        text=f'{{"access_token":"{iam_token}","expires_in":42055,"token_type":"Bearer"}}',
        request=MagicMock(),
    )
    mock_client.get.return_value = response

    metadata = await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert get_auth_meta(metadata) == f"Bearer {iam_token}"


async def test_reissue(async_sdk, auth, monkeypatch, mock_client):
    assert auth._token is None
    assert auth._issue_time is None

    response = httpx.Response(status_code=200, text='{"access_token":"<iam-token-0>"}', request=MagicMock())
    mock_client.get.return_value = response

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-0>"
    assert auth._issue_time is not None

    issue_time = auth._issue_time
    time.sleep(1)

    response = httpx.Response(status_code=200, text='{"access_token":"<iam-token-1>"}', request=MagicMock())
    mock_client.get.return_value = response

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-0>"
    assert auth._issue_time is not None

    monkeypatch.setattr(auth, "_token_refresh_period", 1)

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-1>"
    assert auth._issue_time > issue_time


async def test_applicable_from_env(iam_token, mock_client, monkeypatch):
    response = httpx.Response(status_code=400, request=MagicMock())
    mock_client.get.return_value = response
    assert await MetadataAuth.applicable_from_env() is None
    assert MetadataAuth._default_addr in mock_client.get.call_args[0][0]

    monkeypatch.setenv(MetadataAuth.env_var, "my-unique-addr")
    response = httpx.Response(
        status_code=200,
        text=f'{{"access_token":"{iam_token}","expires_in":42055,"token_type":"Bearer"}}',
        request=MagicMock(),
    )
    mock_client.get.return_value = response

    auth = await MetadataAuth.applicable_from_env()
    assert auth
    assert auth._token == iam_token
    assert "my-unique-addr" in mock_client.get.call_args[0][0]
    assert MetadataAuth._default_addr not in mock_client.get.call_args[0][0]

    mock_client.get.side_effect = httpx.NetworkError("foo")
    assert await MetadataAuth.applicable_from_env() is None
    assert "my-unique-addr" in mock_client.get.call_args[0][0]
