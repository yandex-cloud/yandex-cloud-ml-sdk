from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import grpc.aio
from typing_extensions import override

from yandex_cloud_ml_sdk._auth import BaseAuth
from yandex_cloud_ml_sdk._client import AsyncCloudClient

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class MockClient(AsyncCloudClient):
    def __init__(self, port: int, auth: BaseAuth, sdk: BaseSDK | None = None):
        super().__init__(
            endpoint='test-endpoint',
            auth=auth,
            service_map={},
            interceptors=None,
            yc_profile=None
        )
        self.port = port
        self._sdk = sdk

    @override
    def _new_channel(self, endpoint: str) -> grpc.aio.Channel:
        return grpc.aio.insecure_channel(target=endpoint)

    @override
    async def _init_service_map(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        mock = self._service_map = MagicMock()
        mock.get.return_value = mock.__getitem__.return_value = f'localhost:{self.port}'
