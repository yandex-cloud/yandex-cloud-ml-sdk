# pylint: disable=import-outside-toplevel,no-name-in-module
from __future__ import annotations

import dataclasses

import pytest
from yandex.cloud.ai.assistants.v1.common_pb2 import Tool as ProtoAssistantsTool
from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import Tool as ProtoCompletionsTool

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._tools.function import ParametersType
from yandex_cloud_ml_sdk._tools.tool import FunctionTool


@pytest.mark.require_env('pydantic')
def test_pydantic_model_function_tool(async_sdk: AsyncYCloudML) -> None:
    import pydantic

    etalon = FunctionTool(
        name="Function",
        description="function description",
        parameters={
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "field description",
                    "title": "Field",
                },
            },
            "required": ["field"],
            "title": 'Function',
            "description": 'function description'
        },
        strict=None,
    )

    description: str = (
        etalon.parameters['properties']['field']['description']  # type: ignore[index,call-overload,assignment]
    )

    class Function(pydantic.BaseModel):
        field: str = pydantic.Field(description=description)

    Function.__doc__ = etalon.description

    function_tool = async_sdk.tools.function(Function)
    assert function_tool == etalon

    function_tool = async_sdk.tools.function(Function, name="othern", description="otherd")

    assert function_tool.name == 'othern'
    assert function_tool.description == 'otherd'


@pytest.mark.require_env('pydantic')
def test_pydantic_dataclass_function_tool(async_sdk: AsyncYCloudML) -> None:
    import pydantic.dataclasses

    etalon = FunctionTool(
        name="Function",
        description="function description",
        parameters={
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "field description",
                    "title": "CoolField",
                },
            },
            "required": ["field"],
            "title": 'Function',
            "description": 'function description'
        },
        strict=None,
    )

    description: str = (
        etalon.parameters['properties']['field']['description']  # type: ignore[index,call-overload,assignment]
    )

    @pydantic.dataclasses.dataclass
    class Function:
        field: str = dataclasses.field(
            metadata={
                'title': 'CoolField',
                'description': description,
            },
        )

    Function.__doc__ = etalon.description

    function_tool = async_sdk.tools.function(Function)
    assert function_tool == etalon

    function_tool = async_sdk.tools.function(Function, name="othern", description="otherd")

    assert function_tool.name == 'othern'
    assert function_tool.description == 'otherd'


def test_raw_json_function_tool(async_sdk: AsyncYCloudML) -> None:
    etalon = FunctionTool(
        name="Function",
        description="function description",
        parameters={
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "field description",
                },
            },
            "required": ["field"],
        },
        strict=None,
    )

    parameters = dict(etalon.parameters)
    assert etalon.description

    assert async_sdk.tools.function(parameters, name=etalon.name, description=etalon.description) == etalon

    tool = async_sdk.tools.function(
        {**parameters, **{'title': etalon.name, 'description': etalon.description}}
    )

    assert tool.name == etalon.name
    assert tool.description == etalon.description


def test_bad_types(async_sdk: AsyncYCloudML) -> None:
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "field": {
                "type": "string",
                "description": "field description",
            },
        },
        "required": ["field"],
    }

    async_sdk.tools.function(parameters, name='foo')

    with pytest.raises(TypeError):
        async_sdk.tools.function(parameters)

    with pytest.raises(TypeError):
        async_sdk.tools.function([], name='foo')  # type: ignore[arg-type]


def test_strict(async_sdk: AsyncYCloudML) -> None:
    tool = async_sdk.tools.function({}, name='foo')

    assistant_proto = tool._to_proto(ProtoAssistantsTool)
    assert not hasattr(assistant_proto.function, 'strict')

    assert tool._to_proto(ProtoCompletionsTool).function.strict is False

    for strict in (True, False):
        tool = async_sdk.tools.function({}, name='foo', strict=strict)
        proto = tool._to_proto(ProtoCompletionsTool)
        assert proto.function.strict is strict

        with pytest.raises(ValueError, match='"strict" field is not supported'):
            tool._to_proto(ProtoAssistantsTool)
