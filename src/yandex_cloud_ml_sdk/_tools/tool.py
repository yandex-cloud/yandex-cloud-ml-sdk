# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct
from google.protobuf.wrappers_pb2 import Int64Value
from yandex.cloud.ai.assistants.v1.common_pb2 import FunctionTool as ProtoAssistantsFunctionTool
from yandex.cloud.ai.assistants.v1.common_pb2 import SearchIndexTool as ProtoSearchIndexTool
from yandex.cloud.ai.assistants.v1.common_pb2 import Tool as ProtoAssistantsTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import FunctionTool as ProtoCompletionsFunctionTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Tool as ProtoCompletionsTool

from yandex_cloud_ml_sdk._types.schemas import JsonSchemaType

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


ProtoToolTypeT = TypeVar('ProtoToolTypeT', ProtoAssistantsTool, ProtoCompletionsTool)


class BaseTool(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _from_proto(cls, proto: Any, sdk: BaseSDK) -> BaseTool:
        pass

    @abc.abstractmethod
    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        pass

    @classmethod
    def _from_upper_proto(cls, proto: ProtoToolTypeT, sdk: BaseSDK) -> BaseTool:
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
            return SearchIndexTool._from_proto(
                proto=proto.search_index,
                sdk=sdk
            )
        raise NotImplementedError('tools other then search_index and function are not supported in this SDK version')


@dataclass(frozen=True)
class SearchIndexTool(BaseTool):
    search_index_ids: tuple[str, ...]

    max_num_results: int | None = None

    @classmethod
    def _from_proto(cls, proto: ProtoSearchIndexTool, sdk: BaseSDK) -> SearchIndexTool:
        max_num_results: int | None = None
        if proto.HasField("max_num_results"):
            max_num_results = proto.max_num_results.value

        return cls(
            search_index_ids=tuple(proto.search_index_ids),
            max_num_results=max_num_results,
        )

    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        assert issubclass(proto_type, ProtoAssistantsTool)

        max_num_results: None | Int64Value = None
        if self.max_num_results is not None:
            max_num_results = Int64Value(value=self.max_num_results)

        return proto_type(
            search_index=ProtoSearchIndexTool(
                max_num_results=max_num_results,
                search_index_ids=self.search_index_ids
            )
        )


@dataclass(frozen=True)
class FunctionTool(BaseTool):
    name: str
    description: str | None
    parameters: JsonSchemaType

    @classmethod
    def _from_proto(
        cls,
        proto: ProtoCompletionsFunctionTool | ProtoAssistantsFunctionTool,
        sdk: BaseSDK
    ) -> FunctionTool:
        parameters = MessageToDict(proto.parameters)
        return cls(
            name=proto.name,
            description=proto.description,
            parameters=parameters,
        )

    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        parameters = Struct()
        parameters.update(self.parameters)

        function_class = {
            ProtoAssistantsTool: ProtoAssistantsFunctionTool,
            ProtoCompletionsTool: ProtoCompletionsFunctionTool,
        }[proto_type]

        function = function_class(
            name=self.name,
            description=self.description or '',
            parameters=parameters
        )

        # i dunno how to properly describe this type of polymorphism to mypy
        return proto_type(function=function)  # type: ignore[arg-type]
