from __future__ import annotations

from typing import Any, Literal, TypedDict, Union

from typing_extensions import TypeAlias, TypeGuard

from yandex_cloud_ml_sdk._logging import get_logger

logger = get_logger(__name__)

LITERAL_RESPONSE_TYPES = ('json', )

StrResponseType = Literal['json']
JsonSchemaType = dict[str, Any]

class JsonSchemaResponseType(TypedDict):
    json_schema: JsonSchemaType

ResponseType: TypeAlias = Union[StrResponseType, JsonSchemaResponseType, type]

try:
    import pydantic

    PYDANTIC = True
    PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

except ImportError:
    PYDANTIC = False
    PYDANTIC_V2 = False


def is_pydantic_model_class(response_type: ResponseType) -> TypeGuard[type[pydantic.BaseModel]]:
    return (
        PYDANTIC and
        isinstance(response_type, type) and
        issubclass(response_type, pydantic.BaseModel) and
        not response_type is pydantic.BaseModel
    )


def schema_from_response_type(response_type: ResponseType) -> StrResponseType | JsonSchemaType:
    result: StrResponseType | JsonSchemaType

    if isinstance(response_type, str):
        if not response_type in LITERAL_RESPONSE_TYPES:
            raise ValueError(
                f"Literal response type '{response_type}' is not supported, use one of {LITERAL_RESPONSE_TYPES}")
        result = response_type
    elif isinstance(response_type, dict):
        # TODO: in case we would get jsonschema dependency, it is a good
        # idea to add validation here

        json_schema = response_type.get('json_schema') or response_type.get('jsonschema')
        if json_schema and isinstance(json_schema, dict):
            result = dict(json_schema)
        else:
            raise ValueError(
                'json_schema field must be present in response_type field '
                'and must be a valid json schema dict'
            )
    elif (
        not PYDANTIC or
        not isinstance(response_type, type) or
        not is_pydantic_model_class(response_type) and
        not pydantic.dataclasses.is_pydantic_dataclass(response_type)
    ):
        raise TypeError(
            "Response type could be only str, jsonschema dict or pydantic model class"
        )

    elif is_pydantic_model_class(response_type):
        result = response_type.model_json_schema()
    else:
        assert pydantic.dataclasses.is_pydantic_dataclass(response_type)
        result = pydantic.TypeAdapter(response_type).json_schema()

    logger.debug('transform input response_type=%r to json_schema=%r', response_type, result)
    return result
