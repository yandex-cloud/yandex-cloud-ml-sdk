from __future__ import annotations

from typing import Literal, TypedDict, Union

from typing_extensions import TypeAlias, TypeGuard

from yandex_cloud_ml_sdk._logging import get_logger

logger = get_logger(__name__)

LITERAL_RESPONSE_FORMATS = ('json', )

StrResponseType = Literal['json']

JsonVal = Union[None, bool, str, float, int, 'JsonArray', 'JsonObject']
JsonArray = list[JsonVal]
JsonObject = dict[str, JsonVal]
JsonSchemaType: TypeAlias = JsonObject

class JsonSchemaResponseType(TypedDict):
    json_schema: JsonSchemaType

ResponseType: TypeAlias = Union[StrResponseType, JsonSchemaResponseType, type]
ParametersType: TypeAlias = Union[JsonSchemaType, type]

try:
    import pydantic

    PYDANTIC = True
    PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

except ImportError:
    PYDANTIC = False
    PYDANTIC_V2 = False


def is_pydantic_model_class(response_format: ResponseType) -> TypeGuard[type[pydantic.BaseModel]]:
    return (
        PYDANTIC and
        isinstance(response_format, type) and
        issubclass(response_format, pydantic.BaseModel) and
        not response_format is pydantic.BaseModel
    )


def schema_from_response_format(response_format: ResponseType) -> StrResponseType | JsonSchemaType:
    result: StrResponseType | JsonSchemaType

    if isinstance(response_format, str):
        if not response_format in LITERAL_RESPONSE_FORMATS:
            raise ValueError(
                f"Literal response type '{response_format}' is not supported, use one of {LITERAL_RESPONSE_FORMATS}")
        result = response_format
    elif isinstance(response_format, dict):
        # TODO: in case we would get jsonschema dependency, it is a good
        # idea to add validation here

        json_schema = response_format.get('json_schema') or response_format.get('jsonschema')
        if json_schema and isinstance(json_schema, dict):
            result = dict(json_schema)
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
        result = response_format.model_json_schema()
    else:
        assert pydantic.dataclasses.is_pydantic_dataclass(response_format)
        result = pydantic.TypeAdapter(response_format).json_schema()

    logger.debug('transform input response_format=%r to json_schema=%r', response_format, result)
    return result


def schema_from_parameters(parameters: ParametersType) -> JsonSchemaType:
    if isinstance(parameters, dict):
        result = dict(parameters)
    elif is_pydantic_model_class(parameters):
        result = parameters.model_json_schema()
    elif PYDANTIC and pydantic.dataclasses.is_pydantic_dataclass(parameters):
        result = pydantic.TypeAdapter(parameters).json_schema()
    else:
        raise TypeError(
            "Function call parameters could be only jsonschema dict, pydantuc model class or pydantic dataclass"
        )

    logger.debug('trasform input parameters=%r to json_schema=%r', parameters, result)
    return result
