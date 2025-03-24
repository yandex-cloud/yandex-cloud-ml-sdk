# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Union

from google.protobuf.json_format import MessageToDict
from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import FunctionCall as ProtoAssistantFunctionCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import FunctionCall as ProtoCompletionsFunctionCall

from yandex_cloud_ml_sdk._types.proto import ProtoBased
from yandex_cloud_ml_sdk._types.schemas import JsonObject

ProtoFunctionCall = Union[ProtoAssistantFunctionCall, ProtoCompletionsFunctionCall]


@dataclass(frozen=True)
class BaseFunctionCall(ProtoBased[ProtoFunctionCall]):
    name: str
    arguments: JsonObject
    _proto_origin: ProtoFunctionCall = field(repr=False)

    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoFunctionCall,
        **_,
    ) -> Self:
        return cls(
            name=proto.name,
            arguments=MessageToDict(proto.arguments),
            _proto_origin=proto,
        )


class AsyncFunctionCall(BaseFunctionCall):
    pass


class FunctionCall(BaseFunctionCall):
    pass


FunctionCallTypeT = TypeVar('FunctionCallTypeT', bound=BaseFunctionCall)
