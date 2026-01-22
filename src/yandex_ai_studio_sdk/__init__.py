from __future__ import annotations

from ._logging import setup_default_logging
from ._logging import setup_default_logging_from_env as _setup_default_logging_from_env
from ._sdk import AIStudio, AsyncAIStudio

__version__ = "0.18.0"

__all__ = [
    '__version__',
    'AIStudio',
    'AsyncAIStudio',
    'setup_default_logging',
]

_setup_default_logging_from_env()
