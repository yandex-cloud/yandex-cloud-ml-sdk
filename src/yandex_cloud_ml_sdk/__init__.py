from __future__ import annotations

from ._logging import setup_default_logging
from ._logging import setup_default_logging_from_env as _setup_default_logging_from_env
from ._sdk import AsyncYCloudML, YCloudML

__version__ = "0.9.0"

__all__ = [
    '__version__',
    'YCloudML',
    'AsyncYCloudML',
    'setup_default_logging',
]

_setup_default_logging_from_env()
