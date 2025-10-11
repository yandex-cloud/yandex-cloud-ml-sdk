from __future__ import annotations

from .json import JsonBased
from .proto import ProtoBased, ProtoMessage, ProtoMessageTypeT_contra, SDKType

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseProtoResult', 'SDKType', 'BaseResult', 'BaseJsonResult']


class BaseResult:
    """
    Class for all SDK result objects.

    This is the foundation class for all result types.
    It serves as a common interface for different types of results returned by
    various SDK operations.
    """
    pass


class BaseProtoResult(BaseResult, ProtoBased[ProtoMessageTypeT_contra]):
    """
    Class for Protocol Buffers-based result objects.

    This class combines the base result functionality with Protocol Buffers
    support, providing a foundation for results that need to handle protobuf
    message types.

    :param ProtoMessageTypeT_contra: The Protocol Buffers message type
    """
    pass


class BaseJsonResult(BaseResult, JsonBased):
    """
    Base class for JSON-based result objects.

    This class combines the base result functionality with JSON support,
    providing a foundation for results that handle JSON data structures.
    """
    pass
