from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from google.protobuf.message import Message as ProtoMessage
from typing_extensions import Self, TypeAlias

from yandex_cloud_ml_sdk._utils.proto import proto_to_dict

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


@dataclasses.dataclass(frozen=True)
class ProtoMirrored(ProtoBased[ProtoMessageTypeT_contra]):
    # pylint: disable=unused-argument
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> dict[str, Any]:
        fields = dataclasses.fields(cls)
        data = proto_to_dict(proto)
        kwargs = {}
        for field in fields:
            name = field.name

            if name.startswith('_'):
                continue

            value = data.get(name)

            kwargs[name] = value

        return kwargs

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> Self:
        return cls(
            **cls._kwargs_from_message(proto, sdk=sdk),
        )
