from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import httpx
from typing_extensions import Self, override
from yandex.cloud.iam.v1.iam_token_service_pb2 import (  # pylint: disable=no-name-in-module
    CreateIamTokenRequest, CreateIamTokenResponse
)
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub
from yandex_cloud_ml_sdk._utils.doc import doc_from

if TYPE_CHECKING:
    from ._client import AsyncCloudClient


OAUTH_WARNING = """Sharing your personal OAuth token is not safe,
and gives anyone access to your cloud infrastructure and data.

Use YandexCloudCLIAuth for personal authentication,
MetadataAuth when running your code inside Yandex Cloud infrastructure or
APIKeyAuth for external-hosted automations.

Please, follow our guide if your OAuth-token is leaked
(https://yandex.cloud/en/docs/iam/operations/compromised-credentials)
"""


class BaseAuth(ABC):
    """Abstract base class for authentication methods.

    This class defines the interface for obtaining authentication metadata
    and checking if the authentication method is applicable from environment
    variables.
    """
    @abstractmethod
    async def get_auth_metadata(
        self,
        client: AsyncCloudClient,
        timeout: float,
        lock: asyncio.Lock
    ) -> tuple[str, str] | None:
        """Get authentication metadata.

        :param client: the asynchronous cloud client to use.
        :param timeout: timeout, or the maximum time to wait for the request to complete in seconds.
        :param lock: an asyncio lock to ensure thread safety.

        .. note::
            The lock is reused from the client, as it cannot be created in the Auth constructor.
            See the client's _lock docstring for details.
        """
        # NB: we are can't create lock in Auth constructor, so we a reusing lock from client.
        # Look at client._lock doctstring for details.
        pass

    @classmethod
    @abstractmethod
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        """Check if this authentication method is applicable from environment variables.
        Return an instance of the authentication class if applicable, or None.
        """
        pass


class NoAuth(BaseAuth):
    @override
    @doc_from(BaseAuth.get_auth_metadata)
    async def get_auth_metadata(self, client: AsyncCloudClient, timeout: float, lock: asyncio.Lock) -> None:
        return None

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> None:
        return None


class APIKeyAuth(BaseAuth):
    """Authentication method using an API key."""
    env_var = 'YC_API_KEY'

    def __init__(self, api_key: str):
        """Initialize with an API key.

        :param api_key: The API key to use for authentication.

        .. note::
            If the credential contains a newline character, it may lead to
            a GRPC_CALL_ERROR_INVALID_METADATA error which can be difficult to debug.
        """
        # NB: here and below:
        # if credential with an \n will get into the grpc metadata,
        # user will get very interesting GRPC_CALL_ERROR_INVALID_METADATA error
        # which very funny to debug
        self._api_key = api_key.strip()

    @override
    @doc_from(BaseAuth.get_auth_metadata)
    async def get_auth_metadata(self, client: AsyncCloudClient, timeout: float, lock: asyncio.Lock) -> tuple[str, str]:
        return ('authorization', f'Api-Key {self._api_key}')

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        api_key = os.getenv(cls.env_var)
        if api_key:
            return cls(api_key)

        return None


class BaseIAMTokenAuth(BaseAuth):
    """Base class for IAM token-based authentication."""
    def __init__(self, token: str | None):
        """Initialize with an IAM token.

        :param token: The IAM token to use for authentication. If None, it will be set to None.
        """
        self._token = token.strip() if token else token

    @override
    @doc_from(BaseAuth.get_auth_metadata)
    async def get_auth_metadata(self, client: AsyncCloudClient, timeout: float, lock: asyncio.Lock) -> tuple[str, str]:
        return ('authorization', f'Bearer {self._token}')


class IAMTokenAuth(BaseIAMTokenAuth):
    """Authentication method using an IAM token."""
    env_var = 'YC_IAM_TOKEN'

    def __init__(self, token: str):
        """Initialize with an IAM token.

        :param token: The IAM token to use for authentication.
        """
        super().__init__(token)

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        token = os.getenv(cls.env_var)
        if token:
            return cls(token)

        return None


class EnvIAMTokenAuth(BaseIAMTokenAuth):
    """
    Auth method, which takes IAM token from environment variable for every request.

    It is assumed that the token will be refreshed in the environment before it expires.

    However, by default, the YC_TOKEN environment variable is
    used when auto-selecting the auth method,
    in order to be compatible with a Yandex DataSphere environment.
    Therefore, it is not recommended to use this environment variable
    when setting up a personal work environment.

    """
    default_env_var = 'YC_TOKEN'

    def __init__(self, env_var_name: str | None = None):
        """
        Initializes the authentication method with the specified environment variable name.

        If no environment variable name is provided, the default environment variable
        (YC_TOKEN) is used.
        """
        self._env_var = env_var_name or self.default_env_var
        super().__init__(token=None)

    @override
    @doc_from(BaseAuth.get_auth_metadata)
    async def get_auth_metadata(self, client: AsyncCloudClient, timeout: float, lock: asyncio.Lock) -> tuple[str, str]:
        self._token = os.environ[self._env_var].strip()
        return await super().get_auth_metadata(client=client, timeout=timeout, lock=lock)

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        token = os.getenv(cls.default_env_var)
        if token:
            return cls()

        return None


class RefresheableIAMTokenAuth(BaseIAMTokenAuth):
    """
    Auth method that supports refreshing the IAM token based on a defined refresh period.

    This class manages an IAM token that can be refreshed automatically if it has expired,
    based on the specified refresh period.
    """
    _token_refresh_period = 60 * 60

    def __init__(self, token: str | None) -> None:
        """
        Initializes the authentication method with the provided token.

        Records the issue time of the token if it is provided.
        """
        super().__init__(token)
        self._issue_time: float | None = None
        if self._token is not None:
            self._issue_time = time.time()

    def _need_for_token(self):
        """
        Determines whether a new token is needed based on the current token's status.

        A new token is required if:

        - the current token is None;
        - the issue time is None;
        - the time elapsed since the issue time exceeds the token refresh period.
        """
        return (
            self._token is None or
            self._issue_time is None or
            time.time() - self._issue_time > self._token_refresh_period
        )

    @override
    @doc_from(BaseAuth.get_auth_metadata)
    async def get_auth_metadata(self, client: AsyncCloudClient, timeout: float, lock: asyncio.Lock) -> tuple[str, str]:
        if self._need_for_token():
            async with lock:
                if self._need_for_token():
                    self._token = await self._get_token(client, timeout=timeout)
                    self._issue_time = time.time()

        return await super().get_auth_metadata(client, timeout=timeout, lock=lock)

    @abstractmethod
    async def _get_token(self, client: AsyncCloudClient, timeout: float) -> str:
        """
        Abstract method to retrieve an OAuth token.

        This method must be implemented by subclasses to define how to obtain
        an OAuth token asynchronously.
        """
        pass


class OAuthTokenAuth(RefresheableIAMTokenAuth):
    """
    Auth method that uses an OAuth token for authentication.

    This class extends the RefresheableIAMTokenAuth to provide functionality
    for managing and using an OAuth token for authentication purposes.
    """
    env_var = 'YC_OAUTH_TOKEN'

    def __init__(self, token: str):
        """
        Initializes the OAuthTokenAuth with the provided OAuth token.

        This method also issues a warning regarding the use of OAuth tokens.
        """
        warnings.warn(
            OAUTH_WARNING,
            UserWarning,
        )
        self._oauth_token = token.strip()
        super().__init__(None)

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        token = os.getenv(cls.env_var)
        if token:
            return cls(token)

        return None

    @override
    async def _get_token(self, client: AsyncCloudClient, timeout: float) -> str:
        """
        Retrieve an IAM token asynchronously using the specified client.

        :param client: an instance of AsyncCloudClient used to make the request.
        :param timeout: timeout, or the maximum time to wait for the request to complete in seconds.
        """
        request = CreateIamTokenRequest(yandex_passport_oauth_token=self._oauth_token)
        async with client.get_service_stub(IamTokenServiceStub, timeout=timeout) as stub:
            result = await client.call_service(
                stub.Create,
                request=request,
                timeout=timeout,
                expected_type=CreateIamTokenResponse,
                auth=False,
            )
        return result.iam_token


class YandexCloudCLIAuth(RefresheableIAMTokenAuth):
    """
    Authentication class for Yandex Cloud CLI using IAM tokens.

    It handles the initialization and retrieval of IAM tokens
    via the Yandex Cloud CLI.
    """
    env_var = 'YC_PROFILE'

    def __init__(self, token: str | None = None, endpoint: str | None = None, yc_profile: str | None = None):
        """
        Initialize the YandexCloudCLIAuth instance.

        :param token: the initial IAM token.
        :param endpoint: an endpoint for the Yandex Cloud service.
        :param yc_profile: a Yandex Cloud profile name.
        """
        super().__init__(token)
        self._endpoint = endpoint
        self._yc_profile = yc_profile

    @classmethod
    def _build_command(cls, yc_profile: str | None, endpoint: str | None) -> list[str]:
        """
        Build the command to create an IAM token using the Yandex Cloud CLI.

        :param yc_profile: the Yandex Cloud profile name.
        :param endpoint: the endpoint for the Yandex Cloud service.
        """
        cmd = ['yc', 'iam', 'create-token', '--no-user-output']
        if endpoint:
            cmd.extend(['--endpoint', endpoint])

        if yc_profile:
            cmd.extend(['--profile', yc_profile])

        return cmd

    @classmethod
    async def _check_output(cls, command: list[str]) -> str | None:
        """
        Execute a command and check its output.

        :param command: a list of command arguments to execute.
        """
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        stdout, _ = await process.communicate()
        if process.returncode:
            return None

        if not stdout:
            return ''

        result = stdout.splitlines(keepends=False)
        return result[-1].decode('utf-8')

    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, yc_profile: str | None = None, endpoint: str | None = None, **_: Any) -> Self | None:
        if yc_profile is None:
            yc_profile = os.getenv(cls.env_var)

        if not sys.stdin.isatty():
            return None

        if not shutil.which('yc'):
            return None

        if endpoint:
            endpoint_cmd = ['yc', 'config', 'get', 'endpoint']
            if yc_profile:
                endpoint_cmd.extend(['--profile', yc_profile])

            yc_endpoint = await cls._check_output(endpoint_cmd)
            if yc_endpoint != endpoint:
                return None

        cmd = cls._build_command(yc_profile, endpoint)
        token = await cls._check_output(cmd)
        if token is None:
            return None

        return cls(
            token,
            endpoint=endpoint,
            yc_profile=yc_profile
        )

    @override
    @doc_from(OAuthTokenAuth._get_token)
    async def _get_token(self, client: AsyncCloudClient, timeout: float) -> str:
        cmd = self._build_command(self._yc_profile, self._endpoint)
        if not (token := await self._check_output(cmd)):
            raise RuntimeError('failed to fetch iam token from yc cli')

        return token


class MetadataAuth(RefresheableIAMTokenAuth):
    """
    Authentication class for retrieving IAM tokens from metadata service.

    This class retrieves IAM tokens from the Google Cloud metadata service.
    """
    env_var = 'YC_METADATA_ADDR'
    _headers = {'Metadata-Flavor': 'Google'}
    _default_addr = '169.254.169.254'

    def __init__(self, token: str | None = None, metadata_url: str | None = None):
        """
        Initialize the MetadataAuth instance.

        :param token: the initial IAM token.
        :param metadata_url: URL for the metadata service.
        """
        self._metadata_url: str = metadata_url or self._default_addr
        super().__init__(token)

    @override
    @classmethod
    @doc_from(BaseAuth.applicable_from_env)
    async def applicable_from_env(cls, **_: Any) -> Self | None:
        addr = os.getenv(cls.env_var, cls._default_addr)
        url = f'http://{addr}/computeMetadata/v1/instance/service-accounts/default/token'
        # In case we found env var, we 99% would use this Auth, so timeout became
        # irrelevant
        timeout = 1 if cls.env_var in os.environ else 0.1

        try:
            token = await cls._request_token(timeout, url)
        except (httpx.NetworkError, httpx.HTTPError, json.JSONDecodeError):
            return None

        return cls(token, url)

    @override
    @doc_from(OAuthTokenAuth._get_token)
    async def _get_token(self, client: AsyncCloudClient | None, timeout: float) -> str:
        return await self._request_token(timeout, self._metadata_url)

    @classmethod
    async def _request_token(cls, timeout: float, metadata_url: str) -> str:
        """
        Asynchronously request an IAM access token from the metadata service.

        :param timeout: timeout, or the maximum time to wait for the request to complete in seconds.
        :param metadata_url: the URL of the metadata service to request the token from.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                metadata_url,
                headers=cls._headers,
                timeout=timeout,
            )
            response.raise_for_status()

        data = response.json()
        return data['access_token']


async def get_auth_provider(
    *,
    auth: str | BaseAuth | None,
    endpoint: str,
    yc_profile: str | None,
) -> BaseAuth:
    """
    Retrieve an appropriate authentication provider based on the provided auth parameter.

    It determines the type of authentication to use based on the input
    and returns an instance of a corresponding authentication class.

    :param auth: a string representing the authentication token, an instance of BaseAuth, or None.
    :param endpoint: the endpoint for the Yandex Cloud service.
    :param yc_profile: a Yandex Cloud profile name.
    """
    simple_iam_regexp = re.compile(r'^t\d\.')
    iam_regexp = re.compile(r't1\.[A-Z0-9a-z_-]+[=]{0,2}\.[A-Z0-9a-z_-]{86}[=]{0,2}')
    simple_oauth_regexp = re.compile(r'y[0123]_[-\w]')

    result: BaseAuth | None = None
    if isinstance(auth, str):
        if simple_iam_regexp.match(auth):
            result = IAMTokenAuth(auth)
            if not iam_regexp.match(auth):
                warnings.warn(
                    "auth argument was classified as IAM token but it doesn't match IAM token format; "
                    "in case of any troubles you could create Auth object directly.",
                    UserWarning,
                    stacklevel=2,
                )
        elif simple_oauth_regexp.match(auth):
            result = OAuthTokenAuth(auth)
        else:
            result = APIKeyAuth(auth)
    elif isinstance(auth, BaseAuth):
        result = auth
    elif auth is not None:
        raise RuntimeError(
            'auth argument must be a string (in case of APIKey), instance of BaseAuth or Undefined'
        )
    else:
        for cls in (
            APIKeyAuth,
            IAMTokenAuth,
            OAuthTokenAuth,
            MetadataAuth,
            EnvIAMTokenAuth,
            YandexCloudCLIAuth,
        ):
            result = await cls.applicable_from_env(  # type: ignore[attr-defined]
                yc_profile=yc_profile,
                endpoint=endpoint,
            )
            if result:
                break

    if not result:
        raise RuntimeError(
            'no explicit authorization data was passed and no authorization data was found at environment',
        )

    return result
