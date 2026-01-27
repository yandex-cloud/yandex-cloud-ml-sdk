from __future__ import annotations

from yandex_ai_studio_sdk.exceptions import AioRpcError
from yandex_ai_studio_sdk.exceptions import AIStudioConfigurationError as _AIStudioConfigurationError
from yandex_ai_studio_sdk.exceptions import AIStudioError as _AIStudioError
from yandex_ai_studio_sdk.exceptions import (
    AsyncOperationError, DatasetValidationError, HttpSseError, RunError, TuningError, UnknownEndpointError,
    WrongAsyncOperationStatusError
)

YCloudMLError = _AIStudioError
YCloudMLConfigurationError = _AIStudioConfigurationError

__all__ = [
    'AioRpcError',
    'AsyncOperationError',
    'DatasetValidationError',
    'RunError',
    'TuningError',
    'WrongAsyncOperationStatusError',
    'UnknownEndpointError',
    'HttpSseError',
    'YCloudMLError',
    'YCloudMLConfigurationError',
]
