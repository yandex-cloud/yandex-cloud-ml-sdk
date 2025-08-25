from __future__ import annotations

import inspect
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp  # pylint: disable=no-name-in-module
from typing_extensions import Self

_T = TypeVar('_T')
_D = TypeVar('_D')

_LONG_TYPES = frozenset([
    FieldDescriptor.TYPE_INT64,
    FieldDescriptor.TYPE_SINT64,
    FieldDescriptor.TYPE_UINT64,
    FieldDescriptor.TYPE_FIXED64,
    FieldDescriptor.TYPE_SFIXED64,
])

def proto_to_dict(message: Message) -> dict[str, Any]:
    """
    Convert a protobuf message to a dictionary with proper type handling.
    
    This function converts protobuf messages to dictionaries while handling
    special cases for timestamps and long integer types.
    
    :param message: The protobuf message to convert
    
    .. note::
        Timestamp fields are converted to Python datetime objects.
        Long integer fields are converted to Python int objects.
    """
    dct = MessageToDict(
        message,
        preserving_proto_field_name=True
    )
    for descriptor in message.DESCRIPTOR.fields:
        value = getattr(message, descriptor.name)
        if isinstance(value, Timestamp) and descriptor.name in dct:
            dct[descriptor.name] = value.ToDatetime()
        elif descriptor.type in _LONG_TYPES:
            dct[descriptor.name] = int(value)

    return dct


def get_google_value(
    message: Message,
    field_name: str,
    default: _D,
    expected_type: type[_T],  # pylint: disable=unused-argument
) -> _T | _D:
    """
    Extract a value from a Google protobuf wrapper type.
    
    This function extracts the actual value from Google protobuf wrapper types
    (like google.protobuf.wrappers_pb2.StringValue), returning a default if
    the field is not present.
    
    :param message: The protobuf message containing the field
    :param field_name: Name of the field to extract
    :param default: Default value to return if field is not present
    :param expected_type: Expected type of the extracted value (used for type hints)
    """
    if message.HasField(field_name):
        return cast(_T, getattr(message, field_name).value)

    return cast(_D, default)


def service_for_ctor(stub_ctor: Any) -> str:
    """
    Determine the service ID for a given stub constructor.
    
    This function inspects a gRPC stub constructor to determine which
    Yandex Cloud service it belongs to by analyzing its module name.
    
    :param stub_ctor: The gRPC stub constructor
    """
    m = inspect.getmodule(stub_ctor)
    if m is not None:
        name = m.__name__

        if not name.startswith("yandex.cloud."):
            raise RuntimeError(f"Not a yandex.cloud service {stub_ctor}")

        parts = name.split('.')
        while parts:
            prefix = '.'.join(parts)
            if service_id := _supported_modules.get(prefix):
                return service_id
            parts.pop()

    raise RuntimeError(f"Unknown service {stub_ctor}")


_supported_modules = {
    "yandex.cloud.ai.assistants": "ai-assistants",
    "yandex.cloud.ai.dataset": "ai-foundation-models",
    "yandex.cloud.ai.files": "ai-files",
    "yandex.cloud.ai.foundation_models": "ai-foundation-models",
    "yandex.cloud.ai.llm": "ai-llm",
    "yandex.cloud.ai.ocr": "ai-vision-ocr",
    "yandex.cloud.ai.stt": "ai-stt",
    "yandex.cloud.ai.translate": "ai-translate",
    "yandex.cloud.ai.tts": "ai-speechkit",
    "yandex.cloud.ai.tuning": "ai-foundation-models",
    "yandex.cloud.ai.vision": "ai-vision",
    "yandex.cloud.endpoint": "endpoint",
    "yandex.cloud.iam": "iam",
    "yandex.cloud.operation": "operation",
    "yandex.cloud.searchapi": "searchapi",
    "yandex.cloud.ai.batch_inference": "ai-foundation-models",
}


if TYPE_CHECKING:
    base = Enum
else:
    base = object


class ProtoEnumBase(base):
    """
    Class for protocol buffer enum wrappers.
    
    This class provides functionality for converting between different
    representations of protobuf enum values (string, int, enum instances).
    """

    @classmethod
    def _coerce(cls, value: str | int | ProtoEnumBase) -> Self:
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        if isinstance(value, str):
            if member := cls.__members__.get(value.upper()):
                return member
            raise ValueError(f'wrong value "{value}" for use as an alias for {cls}')
        raise TypeError(f'wrong type "{type(value)}" for use as an alias for {cls}')

    def _to_proto(self) -> int:
        assert hasattr(self, 'value')
        return self.value

    @classmethod
    def _from_proto(cls, proto: int) -> Self:
        try:
            return cls(proto)
        except ValueError:
            return cls(-1)



ProtoEnumTypeT = TypeVar("ProtoEnumTypeT", bound=ProtoEnumBase)
#: Type variable for protobuf enum types that extend ProtoEnumBase.

ProtoEnumCoercible = Union[ProtoEnumTypeT, str, int]
#: Union type for values that can be coerced to a protobuf enum.
