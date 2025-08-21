from __future__ import annotations

from typing import Literal, TypedDict, Union

from typing_extensions import NotRequired, Required, TypeAlias, TypeGuard

from yandex_cloud_ml_sdk._logging import get_logger

logger = get_logger(__name__)

#: Available response formats
LITERAL_RESPONSE_FORMATS = ('json', )

#: Type for string response formats
StrResponseType = Literal['json']

#: Recurrent json object
JsonVal = Union[None, bool, str, float, int, 'JsonArray', 'JsonObject']
#: Json array
JsonArray = list[JsonVal]
#: Json object
JsonObject = dict[str, JsonVal]
#: Type for json schema
JsonSchemaType: TypeAlias = JsonObject

class JsonSchemaResponseType(TypedDict):
    """Dict with json schema response settings"""

    #: Field with json schema which describes response format
    json_schema: JsonSchemaType
    strict: NotRequired[bool]
    name: NotRequired[str]

#: Types availailable for response format
ResponseType: TypeAlias = Union[StrResponseType, JsonSchemaResponseType, type]
#: Types available for function call parameters
ParametersType: TypeAlias = Union[JsonSchemaType, type]

try:
    import pydantic

    PYDANTIC = True
    PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

except ImportError:
    PYDANTIC = False
    PYDANTIC_V2 = False


class JsonObjectProtoFormat(TypedDict):
    json_object: Required[bool]


class JsonSchemaProtoFormat(TypedDict):
    json_schema: Required[JsonSchemaType]


class EmptyProtoFormat(TypedDict):
    pass


class JsonSchemaResponseFormat(TypedDict):
    schema: Required[JsonSchemaType]
    strict: NotRequired[bool]
    name: NotRequired[str]


class JsonSchemaParameterType(TypedDict):
    type: Required[Literal['json_object', 'json_schema']]
    json_schema: NotRequired[JsonSchemaResponseFormat]


def is_pydantic_model_class(response_format: ResponseType) -> TypeGuard[type[pydantic.BaseModel]]:
    return (
        PYDANTIC and
        isinstance(response_format, type) and
        issubclass(response_format, pydantic.BaseModel) and
        not response_format is pydantic.BaseModel
    )


def http_schema_from_response_format(response_format: ResponseType) -> JsonSchemaParameterType:
    result: JsonSchemaParameterType

    if isinstance(response_format, str):
        if not response_format in LITERAL_RESPONSE_FORMATS:
            raise ValueError(
                f"Literal response type '{response_format}' is not supported, use one of {LITERAL_RESPONSE_FORMATS}"
            )

        assert response_format == 'json'
        result = {
            'type': 'json_object'
        }
    elif isinstance(response_format, dict):
        # TODO: in case we would get jsonschema dependency, it is a good
        # idea to add validation here
        json_schema = (
            response_format.get('json_schema') or
            response_format.get('jsonschema') or
            response_format.get('schema')
        )
        if json_schema and isinstance(json_schema, dict):
            result = {
                'type': 'json_schema',
                'json_schema': {
                    'schema': json_schema,
                }
            }
            if name := response_format.get('name'):
                assert isinstance(name, str)
                result['json_schema']['name'] = name

            if 'strict' in response_format:
                result['json_schema']['strict'] = response_format['strict']
        else:
            raise ValueError(
                'json_schema field must be present in response_format field '
                'and must be a valid json schema dict'
            )
    elif (
        not PYDANTIC or
        not isinstance(response_format, type) or
        not is_pydantic_model_class(response_format) and
        not pydantic.dataclasses.is_pydantic_dataclass(response_format)
    ):
        raise TypeError(
            "Response type could be only str, jsonschema dict, pydantic model class or pydantic dataclass"
        )

    elif is_pydantic_model_class(response_format):
        result = {
            'type': 'json_schema',
            'json_schema': {
                'schema': response_format.model_json_schema(),
                'name': response_format.__name__,
                'strict': True,
            },
        }
    else:
        assert pydantic.dataclasses.is_pydantic_dataclass(response_format)
        result = {
            'type': 'json_schema',
            'json_schema': {
                'schema': pydantic.TypeAdapter(response_format).json_schema(),
                'name': response_format.__name__,
                'strict': True,
            },
        }

    logger.debug('transform input response_format=%r to json_schema=%r', response_format, result)
    return result


def make_response_format_kwargs(
    response_format: ResponseType | None
) -> JsonObjectProtoFormat | JsonSchemaProtoFormat | EmptyProtoFormat:
    """
    Here we are transforming
    1) http_schema <- schema_from_response_format(response_format)
    2) grpc_schema <- http_schema
    """
    if response_format is None:
        return {}

    schema = http_schema_from_response_format(response_format)

    type_ = schema['type']
    if type_  == 'json_object':
        return {'json_object': True}
    assert type_ == 'json_schema'
    return {'json_schema': {'schema': schema['json_schema']['schema']}}


def schema_from_parameters(parameters: ParametersType) -> JsonSchemaType:
    if isinstance(parameters, dict):
        result = dict(parameters)
    elif is_pydantic_model_class(parameters):
        result = parameters.model_json_schema()
    elif PYDANTIC and pydantic.dataclasses.is_pydantic_dataclass(parameters):
        result = pydantic.TypeAdapter(parameters).json_schema()
    else:
        raise TypeError(
            "Function call parameters could be only jsonschema dict, pydantic model class or pydantic dataclass"
        )

    logger.debug('trasform input parameters=%r to json_schema=%r', parameters, result)
    return result
