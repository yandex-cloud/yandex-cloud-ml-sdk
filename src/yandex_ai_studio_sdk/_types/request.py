from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .model_config import ConfigTypeT
from .proto import Context


@dataclass(frozen=True)
class RequestDetails(Context, Generic[ConfigTypeT]):
    """:meta private:

    Object to incapsulate model request into result
    to make possible result methods which requires a context"""

    model_config: ConfigTypeT
    timeout: float


RequestDetailsTypeT = TypeVar('RequestDetailsTypeT', bound=RequestDetails)
