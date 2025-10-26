# pylint: disable=no-name-in-module
from __future__ import annotations

import pytest
from yandex.cloud.searchapi.v2.search_query_pb2 import SearchQuery as ProtoSearchQuery

from yandex_cloud_ml_sdk._types.enum import ProtoBasedEnum


# pylint: disable=invalid-enum-extension
class MyTestEnum(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSearchQuery.SearchType
    __common_prefix__ = 'SEARCH_TYPE_'

    RU = ProtoSearchQuery.SearchType.SEARCH_TYPE_RU


def test_coerce():
    for value in (1, 'ru', 'RU', 'SEARCH_type_rU', MyTestEnum.RU):
        assert MyTestEnum._coerce(value) == MyTestEnum.RU

    for value in (2, 'TR', 'tr', 'SEARCH_type_tR', MyTestEnum.Unknown('TR', 2)):
        assert MyTestEnum._coerce(value) == MyTestEnum.Unknown('TR', 2)

    for value in (-10, 'FOO'):
        with pytest.raises(ValueError):
            MyTestEnum._coerce(value)

    for value in ({}, b'FOO', 1.0):
        with pytest.raises(TypeError):
            MyTestEnum._coerce(value)
