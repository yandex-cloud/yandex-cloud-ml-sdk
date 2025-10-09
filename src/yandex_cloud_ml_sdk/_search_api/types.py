# pylint: disable=no-name-in-module
from __future__ import annotations

from yandex.cloud.searchapi.v2.search_query_pb2 import SearchQuery as ProtoSearchQuery
from yandex.cloud.searchapi.v2.search_service_pb2 import GroupSpec as ProtoGroupSpec
from yandex.cloud.searchapi.v2.search_service_pb2 import SortSpec as ProtoSortSpec
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchRequest as ProtoWebSearchRequest

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


class FamilyMode(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSearchQuery.FamilyMode
    __common_prefix__ = 'FAMILY_MODE_'

    NONE = ProtoSearchQuery.FamilyMode.FAMILY_MODE_NONE
    MODERATE = ProtoSearchQuery.FamilyMode.FAMILY_MODE_MODERATE
    STRICT = ProtoSearchQuery.FamilyMode.FAMILY_MODE_STRICT


class FixTypoMode(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSearchQuery.FixTypoMode
    __common_prefix__ = 'FIX_TYPO_MODE_'

    ON = ProtoSearchQuery.FixTypoMode.FIX_TYPO_MODE_ON
    OFF = ProtoSearchQuery.FixTypoMode.FIX_TYPO_MODE_OFF


class SortOrder(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSortSpec.SortOrder
    __common_prefix__ = 'SORT_ORDER_'

    ASC = ProtoSortSpec.SortOrder.SORT_ORDER_ASC
    DESC = ProtoSortSpec.SortOrder.SORT_ORDER_DESC


class SortMode(ProtoBasedEnum):
    __proto_enum_type__ = ProtoSortSpec.SortMode
    __common_prefix__ = 'SORT_MODE_'

    BY_RELEVANCE = ProtoSortSpec.SortMode.SORT_MODE_BY_RELEVANCE
    BY_TIME = ProtoSortSpec.SortMode.SORT_MODE_BY_TIME


class GroupMode(ProtoBasedEnum):
    __proto_enum_type__ = ProtoGroupSpec.GroupMode
    __common_prefix__ = 'GROUP_MODE_'

    FLAT = ProtoGroupSpec.GroupMode.GROUP_MODE_FLAT
    DEEP = ProtoGroupSpec.GroupMode.GROUP_MODE_DEEP


class Localization(ProtoBasedEnum):
    __proto_enum_type__ = ProtoWebSearchRequest.Localization
    __common_prefix__ = 'LOCALIZATION_'

    RU = ProtoWebSearchRequest.Localization.LOCALIZATION_RU
    UK = ProtoWebSearchRequest.Localization.LOCALIZATION_UK
    BE = ProtoWebSearchRequest.Localization.LOCALIZATION_BE
    KK = ProtoWebSearchRequest.Localization.LOCALIZATION_KK
    TR = ProtoWebSearchRequest.Localization.LOCALIZATION_TR
    EN = ProtoWebSearchRequest.Localization.LOCALIZATION_EN


class Format(ProtoBasedEnum):
    __proto_enum_type__ = ProtoWebSearchRequest.Format
    __common_prefix__ = 'FORMAT_'

    XML = ProtoWebSearchRequest.Format.FORMAT_XML
    HTML = ProtoWebSearchRequest.Format.FORMAT_HTML
