# pylint: disable=protected-access
from __future__ import annotations

import time
from unittest.mock import AsyncMock

import pytest

from yandex_cloud_ml_sdk.auth import YandexCloudCLIAuth

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="iam_token")
def fixture_iam_token():
    return "<iam_token>"


@pytest.fixture(name="auth")
def fixture_auth():
    return YandexCloudCLIAuth()


async def test_auth(async_sdk, iam_token, monkeypatch, process_maker, get_auth_meta):
    process = process_maker(stdout=b"Hello\n" + iam_token.encode("utf-8"), stderr=b"")
    mock_create_subprocess_exec = AsyncMock(return_value=process)
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess_exec)

    metadata = await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert get_auth_meta(metadata) == f"Bearer {iam_token}"


async def test_reissue(async_sdk, auth, monkeypatch, process_maker):
    assert auth._token is None
    assert auth._issue_time is None

    process = process_maker(stdout=b"Hello\n<iam-token-0>", stderr=b"")
    mock_create_subprocess_exec = AsyncMock(return_value=process)
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess_exec)

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-0>"
    assert auth._issue_time is not None

    issue_time = auth._issue_time
    time.sleep(1)

    process = process_maker(stdout=b"Hello\n<iam-token-1>", stderr=b"")
    mock_create_subprocess_exec.return_value = process

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-0>"
    assert auth._issue_time is not None

    monkeypatch.setattr(auth, "_token_refresh_period", 1)

    await async_sdk._client._get_metadata(auth_required=True, timeout=1)
    assert auth._token == "<iam-token-1>"
    assert auth._issue_time > issue_time


async def test_applicable_from_env(iam_token, monkeypatch, process_maker):
    async def test(yc_profile=None):
        return await YandexCloudCLIAuth.applicable_from_env(
            endpoint="<test-endpoint>", **({"yc_profile": yc_profile} if yc_profile else {})
        )

    process1 = process_maker(stdout=b"Hello\n<test-endpoint>", stderr=b"")
    process2 = process_maker(stdout=b"Hello\n" + iam_token.encode("utf-8"), stderr=b"")
    mock_create_subprocess_exec = AsyncMock(side_effect=[process1, process2])
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess_exec)

    with monkeypatch.context() as m:
        m.setattr("shutil.which", lambda x: False)
        assert await test() is None
        mock_create_subprocess_exec.assert_not_called()

    with monkeypatch.context() as m:
        m.setattr("sys.stdin.isatty", lambda: False)
        assert await test() is None
        mock_create_subprocess_exec.assert_not_called()

    monkeypatch.setattr("shutil.which", lambda x: True)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    auth = await test()
    assert auth
    assert auth._token == iam_token
    assert mock_create_subprocess_exec.call_count == 2
    assert mock_create_subprocess_exec.call_args_list[0][0] == ("yc", "config", "get", "endpoint")
    assert mock_create_subprocess_exec.call_args_list[1][0] == (
        "yc",
        "iam",
        "create-token",
        "--no-user-output",
        "--endpoint",
        "<test-endpoint>",
    )

    # reset
    mock_create_subprocess_exec = AsyncMock(side_effect=[process1, process2])
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_create_subprocess_exec)
    auth = await test("<test-yc-profile>")
    assert auth
    assert auth._token == iam_token
    assert mock_create_subprocess_exec.call_count == 2
    assert mock_create_subprocess_exec.call_args_list[0][0] == (
        "yc",
        "config",
        "get",
        "endpoint",
        "--profile",
        "<test-yc-profile>",
    )
    assert mock_create_subprocess_exec.call_args_list[1][0] == (
        "yc",
        "iam",
        "create-token",
        "--no-user-output",
        "--endpoint",
        "<test-endpoint>",
        "--profile",
        "<test-yc-profile>",
    )
