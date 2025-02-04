from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from typing_extensions import override

from yandex_cloud_ml_sdk._auth import BaseAuth
from yandex_cloud_ml_sdk._client import AsyncCloudClient
from yandex_cloud_ml_sdk.retry import NoRetryPolicy, RetryPolicy

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

NO_RETRY_DEFAULT = NoRetryPolicy()


class MockClient(AsyncCloudClient):
    def __init__(
        self,
        port: int,
        auth: BaseAuth,
        sdk: BaseSDK | None = None,
        retry_policy: RetryPolicy = NO_RETRY_DEFAULT
    ):
        super().__init__(
            endpoint='test-endpoint',
            auth=auth,
            service_map={},
            interceptors=None,
            yc_profile=None,
            retry_policy=retry_policy,
            enable_server_data_logging=None,
            verify=False,
        )
        self.port = port
        self._sdk = sdk

    @override
    async def _init_service_map(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        mock = self._service_map = MagicMock()
        mock.get.return_value = mock.__getitem__.return_value = f'localhost:{self.port}'
