from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from google.protobuf.message import Message as ProtoMessage
from typing_extensions import Self, TypeAlias

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

    SDKType: TypeAlias = BaseSDK
else:
    SDKType: TypeAlias = Any


ProtoMessageTypeT_contra = TypeVar('ProtoMessageTypeT_contra', bound=ProtoMessage, contravariant=True)
ProtoMessageTypeT = TypeVar('ProtoMessageTypeT', bound=ProtoMessage)


@runtime_checkable
class ProtoBasedType(Protocol[ProtoMessageTypeT_contra]):
    @classmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> Self:
        raise NotImplementedError()


class ProtoBased(abc.ABC, ProtoBasedType[ProtoMessageTypeT_contra]):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> Self:
        raise NotImplementedError()
