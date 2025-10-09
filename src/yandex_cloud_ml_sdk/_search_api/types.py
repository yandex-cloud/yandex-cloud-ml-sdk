# pylint: disable=no-name-in-module
from __future__ import annotations

from yandex.cloud.searchapi.v2.search_query_pb2 import SearchQuery as ProtoSearchQuery

from yandex_cloud_ml_sdk._types.enum import ProtoBasedEnum


class SearchType(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSearchQuery.SearchType
    __common_prefix__ = 'SEARCH_TYPE_'

    RU = ProtoSearchQuery.SearchType.SEARCH_TYPE_RU
    TR = ProtoSearchQuery.SearchType.SEARCH_TYPE_TR
    COM = ProtoSearchQuery.SearchType.SEARCH_TYPE_COM
    KK = ProtoSearchQuery.SearchType.SEARCH_TYPE_KK
    BE = ProtoSearchQuery.SearchType.SEARCH_TYPE_BE
    UZ = ProtoSearchQuery.SearchType.SEARCH_TYPE_UZ
