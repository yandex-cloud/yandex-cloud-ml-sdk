from __future__ import annotations

from .json import JsonBased
from .proto import ProtoBased, ProtoMessage, ProtoMessageTypeT_contra, SDKType

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseProtoResult', 'SDKType', 'BaseResult', 'BaseJsonResult']


class BaseResult:
    pass


class BaseProtoResult(BaseResult, ProtoBased[ProtoMessageTypeT_contra]):
    pass


class BaseJsonResult(BaseResult, JsonBased):
    pass
