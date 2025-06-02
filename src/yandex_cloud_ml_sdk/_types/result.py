from __future__ import annotations

from .proto import ProtoBased, ProtoMessage, ProtoMessageTypeT_contra, SDKType

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseResult', 'SDKType']


class BaseResult(ProtoBased[ProtoMessageTypeT_contra]):
    pass
