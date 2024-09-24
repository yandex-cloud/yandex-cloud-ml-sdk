from __future__ import annotations

from typing import Any

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp


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
