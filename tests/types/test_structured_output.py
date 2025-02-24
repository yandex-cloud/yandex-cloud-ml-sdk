# pylint: disable=import-outside-toplevel,protected-access
from __future__ import annotations

import dataclasses
import sys
import typing

import pytest

import yandex_cloud_ml_sdk._types.structured_output
from yandex_cloud_ml_sdk._types.structured_output import schema_from_response_format


def test_string_type() -> None:
    assert schema_from_response_format('json') == 'json'
    with pytest.raises(ValueError):
        schema_from_response_format('yaml')  # type: ignore[arg-type]


def test_dict_type() -> None:
    assert schema_from_response_format({"json_schema": {"foo": "bar"}}) == {"foo": "bar"}
    with pytest.raises(ValueError):
        schema_from_response_format({"foo": "bar"})  # type: ignore[arg-type]


@pytest.mark.require_env('pydantic')
def test_pydantic_model() -> None:
    assert yandex_cloud_ml_sdk._types.structured_output.PYDANTIC is True

    import pydantic

    class TestInternal(pydantic.BaseModel):
        a: int

    class Test(pydantic.BaseModel):
        b: float
        c: list[TestInternal]

    assert schema_from_response_format(Test) == {
        '$defs': {
            'TestInternal': {
                'properties': {'a': {'title': 'A', 'type': 'integer'}},
                'required': ['a'],
                'title': 'TestInternal',
                'type': 'object'
            }
        },
        'properties': {
            'b': {'title': 'B', 'type': 'number'},
            'c': {
                'items': {'$ref': '#/$defs/TestInternal'},
                'title': 'C',
                'type': 'array'}
        },
       'required': ['b', 'c'],
       'title': 'Test',
       'type': 'object'
    }


@pytest.mark.require_env('pydantic')
def test_pydantic_dataclass() -> None:
    import pydantic

    @pydantic.dataclasses.dataclass
    class TestInternal:
        a: int

    @pydantic.dataclasses.dataclass
    class Test:
        b: float
        c: list[TestInternal]

    pydantic.dataclasses.rebuild_dataclass(Test)  # type: ignore[arg-type]

    assert schema_from_response_format(Test) == {
        '$defs': {
            'TestInternal': {
                'properties': {'a': {'title': 'A', 'type': 'integer'}},
                'required': ['a'],
                'title': 'TestInternal',
                'type': 'object'
            }
        },
        'properties': {
            'b': {'title': 'B', 'type': 'number'},
            'c': {
                'items': {'$ref': '#/$defs/TestInternal'},
                'title': 'C',
                'type': 'array'}
        },
       'required': ['b', 'c'],
       'title': 'Test',
       'type': 'object'
    }


def test_wrong_type() -> None:
    class A:
        a: int

    @dataclasses.dataclass
    class B:
        a: int

    with pytest.raises(TypeError):
        schema_from_response_format(1)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        schema_from_response_format(A)

    with pytest.raises(TypeError):
        schema_from_response_format(B)


@pytest.fixture(name='no_pydantic')
def fixture_no_pydantic(monkeypatch) -> typing.Iterator[bool]:
    # pylint: disable=reimported
    sys.modules.pop(yandex_cloud_ml_sdk._types.structured_output.__name__, None)

    with monkeypatch.context() as m:
        m.setitem(sys.modules, 'pydantic', None)
        import yandex_cloud_ml_sdk._types.structured_output as _m

        yield True

    sys.modules.pop(yandex_cloud_ml_sdk._types.structured_output.__name__, None)
    import yandex_cloud_ml_sdk._types.structured_output as _m2

    assert _m
    assert _m2


def test_no_pydantic(no_pydantic) -> None:
    assert no_pydantic
    assert yandex_cloud_ml_sdk._types.structured_output.PYDANTIC is False
    assert yandex_cloud_ml_sdk._types.structured_output.PYDANTIC_V2 is False

    class A:
        a: int

    with pytest.raises(TypeError):
        schema_from_response_format(A)
