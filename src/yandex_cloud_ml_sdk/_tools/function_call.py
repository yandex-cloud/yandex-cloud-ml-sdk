# pylint: disable=no-name-in-module
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TypeVar, Union

from google.protobuf.json_format import MessageToDict
from typing_extensions import Self
from yandex.cloud.ai.assistants.v1.common_pb2 import FunctionCall as ProtoAssistantFunctionCall
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import FunctionCall as ProtoCompletionsFunctionCall

from yandex_cloud_ml_sdk._types.json import JsonBased
from yandex_cloud_ml_sdk._types.proto import ProtoBased, SDKType
from yandex_cloud_ml_sdk._types.schemas import JsonObject
from yandex_cloud_ml_sdk._utils.doc import doc_from

ProtoFunctionCall = Union[ProtoAssistantFunctionCall, ProtoCompletionsFunctionCall]


@dataclass(frozen=True)
class BaseFunctionCall(JsonBased, ProtoBased[ProtoFunctionCall]):
    """
    Represents a function call returned by models as a result of server-side tool calls.

    This class encapsulates the details of a function call that was invoked by the model
    during processing, including the function name and the arguments passed to it.
    """
    #: Name of the function being called
    name: str
    #: Arguments passed to the function
    arguments: JsonObject
    _proto_origin: ProtoFunctionCall | None = field(repr=False)

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

    @classmethod
    def _from_json(cls, *, data: JsonObject, sdk: SDKType) -> Self:
        name = data.get('name', '<unknown>')
        assert isinstance(name, str)
        raw_arguments = data.get('arguments')
        assert isinstance(raw_arguments, str)

        return cls(
            name=name,
            arguments=json.loads(raw_arguments),
            _proto_origin=None,
        )


@doc_from(BaseFunctionCall)
class AsyncFunctionCall(BaseFunctionCall):
    pass


@doc_from(BaseFunctionCall)
class FunctionCall(BaseFunctionCall):
    pass


#: Type variable representing any function call type.
FunctionCallTypeT = TypeVar('FunctionCallTypeT', bound=BaseFunctionCall)

