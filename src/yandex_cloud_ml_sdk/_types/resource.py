from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseResource:
    # TODO: add some repr, description and such
    def __init__(self, name: str, sdk: BaseSDK):
        self._name = name
        self._sdk = sdk
