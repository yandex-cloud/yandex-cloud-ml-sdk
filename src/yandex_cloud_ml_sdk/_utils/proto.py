from __future__ import annotations

from typing import Any, TypeVar, cast

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp  # pylint: disable=no-name-in-module

_T = TypeVar('_T')
_D = TypeVar('_D')


def proto_to_dict(message: Message) -> dict[str, Any]:
    dct = MessageToDict(
        message,
        preserving_proto_field_name=True
    )
    for descriptor in message.DESCRIPTOR.fields:
        value = getattr(message, descriptor.name)
        if isinstance(value, Timestamp):
            dct[descriptor.name] = value.ToDatetime()
    return dct


def get_google_value(
    message: Message,
    field_name: str,
    default: _D,
    expected_type: type[_T],  # pylint: disable=unused-argument
) -> _T | _D:
    if message.HasField(field_name):
        return cast(_T, getattr(message, field_name).value)

    return cast(_D, default)
