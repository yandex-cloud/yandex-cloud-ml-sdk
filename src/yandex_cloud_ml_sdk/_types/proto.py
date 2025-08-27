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
    """
    Protocol for types that can be created from protobuf messages.

    This protocol defines the interface for classes that can be instantiated
    from Protocol Buffer messages using the SDK context.

    :param ProtoMessageTypeT_contra: The protobuf message type (contravariant)
    """

    @classmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> Self:
        raise NotImplementedError()


class ProtoBased(abc.ABC, ProtoBasedType[ProtoMessageTypeT_contra]):
    """
    Abstract base class for types based on protobuf messages.

    This class provides a concrete implementation of the ProtoBasedType protocol
    and serves as a base class for SDK types that are derived from Protocol Buffer
    messages.

    :param ProtoMessageTypeT_contra: The protobuf message type (contravariant)
    """

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT_contra, sdk: BaseSDK) -> Self:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class ProtoMirrored(ProtoBased[ProtoMessageTypeT_contra]):
    """
    A dataclass that mirrors protobuf message fields.

    This class automatically maps protobuf message fields to dataclass fields
    with the same names. It provides a convenient way to create immutable SDK
    types that directly correspond to protobuf message structures.

    :param ProtoMessageTypeT_contra: The protobuf message type (contravariant)
    """

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
