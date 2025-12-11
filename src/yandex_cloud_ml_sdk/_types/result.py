from __future__ import annotations

from .json import JsonBased
from .proto import ProtoBased, ProtoBasedWithCtx, ProtoMessage, ProtoMessageTypeT_contra, SDKType
from .request import RequestDetailsTypeT

# it is left here until further refactoring
__all__ = ['ProtoMessage', 'BaseProtoResult', 'SDKType', 'BaseResult', 'BaseJsonResult']


class BaseResult:
    pass


class BaseProtoResult(BaseResult, ProtoBased[ProtoMessageTypeT_contra]):
    pass


class BaseProtoModelResult(
    BaseResult,
    ProtoBasedWithCtx[ProtoMessageTypeT_contra, RequestDetailsTypeT],
):
    pass

class BaseJsonResult(BaseResult, JsonBased):
    pass
