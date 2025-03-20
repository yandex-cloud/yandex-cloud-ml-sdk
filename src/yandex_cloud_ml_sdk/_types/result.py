from __future__ import annotations

from .proto import ProtoBased, ProtoMessage, ProtoMessageTypeT_contra

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseResult']


class BaseResult(ProtoBased[ProtoMessageTypeT_contra]):
    pass
