# pylint: disable=protected-access
from __future__ import annotations

import time
import warnings

import pytest
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenResponse  # pylint: disable=no-name-in-module
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import (
    IamTokenServiceServicer, add_IamTokenServiceServicer_to_server
)

from yandex_cloud_ml_sdk.auth import OAuthTokenAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="oauth_token")
def fixture_oauth_token():
    return "<oauth_token>"


@pytest.fixture(name="auth")
def fixture_auth(oauth_token):
    return OAuthTokenAuth(oauth_token)


@pytest.fixture
def servicers(oauth_token):
    class Servicer(IamTokenServiceServicer):
        def __init__(self):
            self.i = 0

        def Create(self, request, context):
            assert request.yandex_passport_oauth_token == oauth_token

            response = CreateIamTokenResponse(iam_token=f"<iam-token-{self.i}>")
            self.i += 1
            return response

    return [(Servicer(), add_IamTokenServiceServicer_to_server)]


@pytest.mark.filterwarnings("ignore:.*OAuth:UserWarning")
async def test_auth(async_sdk, auth, get_auth_meta):
    metadata = await async_sdk._client._get_metadata(auth_required=True, timeout=1)

    assert auth._issue_time is not None
    assert get_auth_meta(metadata) == "Bearer <iam-token-0>"


@pytest.mark.filterwarnings(r"ignore:.*OAuth:UserWarning")
async def test_reissue(async_sdk, auth, monkeypatch):
    assert auth._token is None
    assert auth._issue_time is None

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-0>"
    assert auth._issue_time is not None

    issue_time = auth._issue_time
    time.sleep(1)

    # no reissue after second request
    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._issue_time == issue_time
    assert auth._token == "<iam-token-0>"

    # now we will trigger reissue of a token
    monkeypatch.setattr(auth, "_token_refresh_period", 1)

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-1>"
    assert auth._issue_time > issue_time


async def test_applicable_from_env(oauth_token, monkeypatch):
    monkeypatch.delenv(OAuthTokenAuth.env_var, raising=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert await OAuthTokenAuth.applicable_from_env() is None

    monkeypatch.setenv(OAuthTokenAuth.env_var, oauth_token)
    with pytest.warns(UserWarning, match=r'Sharing'):
        auth = await OAuthTokenAuth.applicable_from_env()
    assert auth
    assert auth._oauth_token == oauth_token
