# pylint: disable=protected-access
from __future__ import annotations

import os
import unittest.mock

import httpx
import pytest

from yandex_cloud_ml_sdk._auth import get_auth_provider
from yandex_cloud_ml_sdk.auth import (
    APIKeyAuth, EnvIAMTokenAuth, IAMTokenAuth, MetadataAuth, NoAuth, OAuthTokenAuth, YandexCloudCLIAuth
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def clear_env(monkeypatch, mock_client):
    mock_client.get.side_effect = httpx.NetworkError('')

    monkeypatch.setattr('shutil.which', lambda x: False)
    monkeypatch.setattr('sys.stdin.isatty', lambda: True)
    with unittest.mock.patch.dict(os.environ, clear=True):
        yield


async def test_clear_env():
    with pytest.raises(RuntimeError, match=r'no explicit authorization data'):
        await get_auth_provider(auth=None, endpoint=None, yc_profile=None)


async def test_input_data(monkeypatch):
    monkeypatch.setenv(APIKeyAuth.env_var, 'foo')

    with pytest.raises(RuntimeError, match=r'auth argument must be'):
        await get_auth_provider(auth=1, endpoint=None, yc_profile=None)

    auth = await get_auth_provider(auth='str', endpoint=None, yc_profile=None)
    assert isinstance(auth, APIKeyAuth)

    with pytest.warns(UserWarning, match=r"auth argument was classified as IAM"):
        auth = await get_auth_provider(auth='t2.foo', endpoint=None, yc_profile=None)
    assert isinstance(auth, IAMTokenAuth)

    auth = await get_auth_provider(auth=NoAuth(), endpoint=None, yc_profile=None)
    assert isinstance(auth, NoAuth)

    with pytest.warns(UserWarning, match=r"Sharing your personal OAuth token is not safe"):
        auth = await get_auth_provider(
            auth="y3_ABC-_-abc123",
            endpoint=None,
            yc_profile=None
        )
    assert isinstance(auth, OAuthTokenAuth)


@pytest.mark.filterwarnings(r"ignore:.*OAuth:UserWarning")
async def test_order(monkeypatch, mock_client, process_maker):
    with pytest.raises(RuntimeError):
        await get_auth_provider(auth=None, endpoint=None, yc_profile=None)

    iam_token = '<iam_token>'

    monkeypatch.setattr('shutil.which', lambda x: True)
    process1 = process_maker(stdout=b"Hello\n<test-endpoint>", stderr=b"")
    process2 = process_maker(stdout=b"Hello\n" + iam_token.encode("utf-8"), stderr=b"")
    mock_create_subprocess_exec = unittest.mock.AsyncMock(side_effect=[process1, process2])
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess_exec)
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, YandexCloudCLIAuth)

    monkeypatch.setenv(EnvIAMTokenAuth.default_env_var, iam_token)
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, EnvIAMTokenAuth)

    response = httpx.Response(
        status_code=200,
        text=f'{{"access_token":"{iam_token}","expires_in":42055,"token_type":"Bearer"}}',
        request=unittest.mock.MagicMock(),
    )
    mock_client.get.return_value = response
    mock_client.get.side_effect = None
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, MetadataAuth)

    monkeypatch.setenv(OAuthTokenAuth.env_var, 'foo')
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, OAuthTokenAuth)

    monkeypatch.setenv(IAMTokenAuth.env_var, iam_token)
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, IAMTokenAuth)

    monkeypatch.setenv(APIKeyAuth.env_var, 'foo')
    auth = await get_auth_provider(auth=None, endpoint=None, yc_profile=None)
    assert isinstance(auth, APIKeyAuth)

    auth = await get_auth_provider(auth=NoAuth(), endpoint=None, yc_profile=None)
    assert isinstance(auth, NoAuth)
