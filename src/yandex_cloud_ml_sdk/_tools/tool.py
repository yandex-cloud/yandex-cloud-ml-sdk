# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TypeVar, Union

from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct
from yandex.cloud.ai.assistants.v1.common_pb2 import FunctionTool as ProtoAssistantsFunctionTool
from yandex.cloud.ai.assistants.v1.common_pb2 import Tool as ProtoAssistantsTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import FunctionTool as ProtoCompletionsFunctionTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Tool as ProtoCompletionsTool

from yandex_cloud_ml_sdk._types.proto import ProtoBased, ProtoMessageTypeT, SDKType
from yandex_cloud_ml_sdk._types.schemas import JsonSchemaType

ProtoToolTypeT = TypeVar('ProtoToolTypeT', ProtoAssistantsTool, ProtoCompletionsTool)
"""
Type variable representing protobuf tool types.
"""


class BaseTool(ProtoBased[ProtoMessageTypeT]):
    """
    Base class for all tools in Yandex Cloud ML SDK.
    """

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, *, proto: ProtoMessageTypeT, sdk: SDKType) -> BaseTool:
        """
        Create tool instance from protobuf message.

        :param proto: Protobuf message to convert
        :param sdk: SDK instance
        """
        pass

    @abc.abstractmethod
    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        """Convert tool to protobuf message.

        :param proto_type: Protobuf message type to create
        """
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoToolTypeT, sdk: SDKType) -> BaseTool:
        """Create tool instance from upper-level protobuf message.

        :param proto: Protobuf message to convert
        :param sdk: SDK instance
        """
        if proto.HasField('function'):
            return FunctionTool._from_proto(
                proto=proto.function,
                sdk=sdk
            )

        # Because of weird polymorphism
        if (
            hasattr(proto, 'search_index') and
            proto.HasField('search_index')  # type: ignore[arg-type]
        ):
            # pylint: disable=import-outside-toplevel
            from .search_index.tool import SearchIndexTool

            return SearchIndexTool._from_proto(
                proto=proto.search_index,
                sdk=sdk
            )
        raise NotImplementedError('tools other then search_index and function are not supported in this SDK version')


ProtoFunctionTool = Union[ProtoCompletionsFunctionTool, ProtoAssistantsFunctionTool]
"""
Union type for function tool protobuf messages.
"""


@dataclass(frozen=True)
class FunctionTool(BaseTool[ProtoFunctionTool]):
    """
    Function tool representation in Yandex Cloud ML SDK.
    """
    #: Name of the function
    name: str
    #: Optional function description
    description: str | None
    #: Function parameters schema
    parameters: JsonSchemaType
    #: Whether to enforce strict parameter validation
    strict: bool | None

    # pylint: disable=unused-argument
    @classmethod
    def _from_proto(
        cls,
        *,
        proto: ProtoFunctionTool,
        sdk:SDKType,
    ) -> FunctionTool:
        """
        Create FunctionTool from protobuf message.

        :param proto: Protobuf message to convert
        :param sdk: SDK instance
        """
        parameters = MessageToDict(proto.parameters)

        strict: bool | None = None
        if hasattr(proto, 'strict'):
            strict = proto.strict

        return cls(
            name=proto.name,
            description=proto.description,
            parameters=parameters,
            strict=strict,
        )

    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        """Convert FunctionTool to protobuf message.

        :param proto_type: Protobuf message type to create
        :raises ValueError: If strict validation is not supported for the proto type
        """
        parameters = Struct()
        parameters.update(self.parameters)

        function_class = {
            ProtoAssistantsTool: ProtoAssistantsFunctionTool,
            ProtoCompletionsTool: ProtoCompletionsFunctionTool,
        }[proto_type]

        additional_kwargs = {}
        # TODO: remove this logic after strict would be supported in assistants
        if self.strict is not None:
            strict_field_present = 'strict' in {
                field.name
                for field in function_class.DESCRIPTOR.fields  # type: ignore[attr-defined]
            }
            if strict_field_present:
                additional_kwargs['strict'] = self.strict
            else:
                raise ValueError(
                    '"strict" field is not supported in sdk.assistants yet, only in sdk.models.completions'
                )

        function = function_class(
            name=self.name,
            description=self.description or '',
            parameters=parameters,
            **additional_kwargs,
        )

        # i dunno how to properly describe this type of polymorphism to mypy
        return proto_type(function=function)  # type: ignore[arg-type]
