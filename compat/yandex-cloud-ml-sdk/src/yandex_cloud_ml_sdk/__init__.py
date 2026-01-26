"""isort:skip_file"""

import os

os.putenv('_YANDEX_AI_STUDIO_NO_LOGGING_SETUP', '1')

# pylint: disable=wrong-import-position
from yandex_ai_studio_sdk import (
    AIStudio as _AIStudio,
    AsyncAIStudio as _AsyncAIStudio,
)
from yandex_ai_studio_sdk._logging.utils import (
    setup_default_logging_from_env as _setup_default_logging_from_env,
)
from ._logging import setup_default_logging, setup_log_relay as _setup_log_relay

os.unsetenv('_YANDEX_AI_STUDIO_NO_LOGGING_SETUP')

_setup_default_logging_from_env('yandex_cloud_ml_sdk')
_setup_log_relay()


class YCloudML(_AIStudio):
    _logger_name = 'yandex_cloud_ml_sdk'


class AsyncYCloudML(_AsyncAIStudio):
    _logger_name = 'yandex_cloud_ml_sdk'


__version__ = '0.19.0'

__all__ = [
    '__version__',
    'YCloudML',
    'AsyncYCloudML',
    'setup_default_logging',
]
