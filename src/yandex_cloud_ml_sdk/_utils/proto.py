from __future__ import annotations

import inspect
from typing import Any, TypeVar, cast

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp  # pylint: disable=no-name-in-module

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
    dct = MessageToDict(
        message,
        preserving_proto_field_name=True
    )
    for descriptor in message.DESCRIPTOR.fields:
        value = getattr(message, descriptor.name)
        if isinstance(value, Timestamp):
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
    if message.HasField(field_name):
        return cast(_T, getattr(message, field_name).value)

    return cast(_D, default)


def service_for_ctor(stub_ctor: Any) -> str:
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
    "yandex.cloud.ai.vision": "ai-vision",
    "yandex.cloud.endpoint": "endpoint",
    "yandex.cloud.operation": "operation",
    "yandex.cloud.iam": "iam",
}
