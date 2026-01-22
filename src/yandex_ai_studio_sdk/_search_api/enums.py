# pylint: disable=no-name-in-module,invalid-enum-extension
from __future__ import annotations

from yandex.cloud.searchapi.v2.img_search_service_pb2 import ImageSpec as ProtoImageSpec
from yandex.cloud.searchapi.v2.search_query_pb2 import SearchQuery as ProtoSearchQuery
from yandex.cloud.searchapi.v2.search_service_pb2 import GroupSpec as ProtoGroupSpec
from yandex.cloud.searchapi.v2.search_service_pb2 import SortSpec as ProtoSortSpec
from yandex.cloud.searchapi.v2.search_service_pb2 import WebSearchRequest as ProtoWebSearchRequest

from yandex_ai_studio_sdk._types.enum import ProtoBasedEnum


class SearchType(ProtoBasedEnum):
    """Search type."""
    __proto_enum_type__ = ProtoSearchQuery.SearchType
    __common_prefix__ = 'SEARCH_TYPE_'

    __aliases__ = {
        'BY': 'BE',
        'KK': 'KZ',
    }

    RU = ProtoSearchQuery.SearchType.SEARCH_TYPE_RU
    TR = ProtoSearchQuery.SearchType.SEARCH_TYPE_TR
    COM = ProtoSearchQuery.SearchType.SEARCH_TYPE_COM
    KK = ProtoSearchQuery.SearchType.SEARCH_TYPE_KK
    BE = ProtoSearchQuery.SearchType.SEARCH_TYPE_BE
    UZ = ProtoSearchQuery.SearchType.SEARCH_TYPE_UZ


class FamilyMode(ProtoBasedEnum):
    """Results filtering."""
    __proto_enum_type__ = ProtoSearchQuery.FamilyMode
    __common_prefix__ = 'FAMILY_MODE_'

    #: Filtering is disabled. Search results include any documents regardless of their contents.
    NONE = ProtoSearchQuery.FamilyMode.FAMILY_MODE_NONE
    #: Moderate filter (default value). Documents of the Adult category are excluded from search results
    #: unless a query is explicitly made for searching resources of this category.
    MODERATE = ProtoSearchQuery.FamilyMode.FAMILY_MODE_MODERATE
    #: Regardless of a search query, documents of the Adult category
    #: and those with profanity are excluded from search results.
    STRICT = ProtoSearchQuery.FamilyMode.FAMILY_MODE_STRICT


class FixTypoMode(ProtoBasedEnum):
    """Search query typo correction setting"""
    __proto_enum_type__ = ProtoSearchQuery.FixTypoMode
    __common_prefix__ = 'FIX_TYPO_MODE_'

    #: Automatically correct typos (default value).
    ON = ProtoSearchQuery.FixTypoMode.FIX_TYPO_MODE_ON
    #: Autocorrection is off.
    OFF = ProtoSearchQuery.FixTypoMode.FIX_TYPO_MODE_OFF


class SortOrder(ProtoBasedEnum):
    """Search results sorting order"""
    __proto_enum_type__ = ProtoSortSpec.SortOrder
    __common_prefix__ = 'SORT_ORDER_'

    #: Reverse order from oldest to most recent.
    ASC = ProtoSortSpec.SortOrder.SORT_ORDER_ASC
    #: Direct order from most recent to oldest (default).
    DESC = ProtoSortSpec.SortOrder.SORT_ORDER_DESC


class SortMode(ProtoBasedEnum):
    """Search results sorting mode rule"""
    __proto_enum_type__ = ProtoSortSpec.SortMode
    __common_prefix__ = 'SORT_MODE_'

    #: Sort documents by relevance (default value).
    BY_RELEVANCE = ProtoSortSpec.SortMode.SORT_MODE_BY_RELEVANCE
    #: Sort documents by update time.
    BY_TIME = ProtoSortSpec.SortMode.SORT_MODE_BY_TIME


class GroupMode(ProtoBasedEnum):
    """Result grouping method."""
    __proto_enum_type__ = ProtoGroupSpec.GroupMode
    __common_prefix__ = 'GROUP_MODE_'

    #: Flat grouping. Each group contains a single document.
    FLAT = ProtoGroupSpec.GroupMode.GROUP_MODE_FLAT
    #: Grouping by domain. Each group contains documents from one domain.
    DEEP = ProtoGroupSpec.GroupMode.GROUP_MODE_DEEP


class Localization(ProtoBasedEnum):
    """Maximum number of groups that can be returned per page."""
    __proto_enum_type__ = ProtoWebSearchRequest.Localization
    __common_prefix__ = 'LOCALIZATION_'

    RU = ProtoWebSearchRequest.Localization.LOCALIZATION_RU
    UK = ProtoWebSearchRequest.Localization.LOCALIZATION_UK
    BE = ProtoWebSearchRequest.Localization.LOCALIZATION_BE
    KK = ProtoWebSearchRequest.Localization.LOCALIZATION_KK
    TR = ProtoWebSearchRequest.Localization.LOCALIZATION_TR
    EN = ProtoWebSearchRequest.Localization.LOCALIZATION_EN


class Format(ProtoBasedEnum):
    """Search result format"""
    __proto_enum_type__ = ProtoWebSearchRequest.Format
    __common_prefix__ = 'FORMAT_'

    XML = ProtoWebSearchRequest.Format.FORMAT_XML
    HTML = ProtoWebSearchRequest.Format.FORMAT_HTML


class ImageFormat(ProtoBasedEnum):
    __proto_enum_type__ = ProtoImageSpec.ImageFormat
    __common_prefix__ = 'IMAGE_FORMAT_'

    #: JPG format.
    JPEG = ProtoImageSpec.ImageFormat.IMAGE_FORMAT_JPEG
    #: GIF format.
    GIF = ProtoImageSpec.ImageFormat.IMAGE_FORMAT_GIF
    #: PNG format.
    PNG = ProtoImageSpec.ImageFormat.IMAGE_FORMAT_PNG


class ImageOrientation(ProtoBasedEnum):
    __proto_enum_type__ = ProtoImageSpec.ImageOrientation
    __common_prefix__ = 'IMAGE_ORIENTATION_'

    #: Horizontal orientation.
    VERTICAL = ProtoImageSpec.ImageOrientation.IMAGE_ORIENTATION_VERTICAL
    #: Vertical orientation.
    HORIZONTAL = ProtoImageSpec.ImageOrientation.IMAGE_ORIENTATION_HORIZONTAL
    #: Square aspect ratio.
    SQUARE = ProtoImageSpec.ImageOrientation.IMAGE_ORIENTATION_SQUARE


class ImageSize(ProtoBasedEnum):
    __proto_enum_type__ = ProtoImageSpec.ImageSize
    __common_prefix__ = 'IMAGE_SIZE_'

    #: Very large images (larger than 1,600 × 1,200 pixels).
    ENORMOUS = ProtoImageSpec.ImageSize.IMAGE_SIZE_ENORMOUS
    #: Large images (from 800 × 600 to 1,600 × 1,200 pixels).
    LARGE = ProtoImageSpec.ImageSize.IMAGE_SIZE_LARGE
    #: Medium images (from 150 × 150 to 800 × 600 pixels).
    MEDIUM = ProtoImageSpec.ImageSize.IMAGE_SIZE_MEDIUM
    #: Small images (from 32 × 32 to 150 × 150 pixels).
    SMALL = ProtoImageSpec.ImageSize.IMAGE_SIZE_SMALL
    #: Icons (up to 32 × 32 pixels).
    TINY = ProtoImageSpec.ImageSize.IMAGE_SIZE_TINY
    #: Desktop wallpapers.
    WALLPAPER = ProtoImageSpec.ImageSize.IMAGE_SIZE_WALLPAPER


class ImageColor(ProtoBasedEnum):
    __proto_enum_type__ = ProtoImageSpec.ImageColor
    __common_prefix__ = 'IMAGE_COLOR_'

    #: Color images.
    COLOR = ProtoImageSpec.ImageColor.IMAGE_COLOR_COLOR
    #: Black and white images.
    GRAYSCALE = ProtoImageSpec.ImageColor.IMAGE_COLOR_GRAYSCALE
    #: Red is the main color of the image.
    RED = ProtoImageSpec.ImageColor.IMAGE_COLOR_RED
    #: Orange is the main color of the image.
    ORANGE = ProtoImageSpec.ImageColor.IMAGE_COLOR_ORANGE
    #: Yellow is the main color of the image.
    YELLOW = ProtoImageSpec.ImageColor.IMAGE_COLOR_YELLOW
    #: Green is the main color of the image.
    GREEN = ProtoImageSpec.ImageColor.IMAGE_COLOR_GREEN
    #: Cyan is the main color of the image.
    CYAN = ProtoImageSpec.ImageColor.IMAGE_COLOR_CYAN
    #: Blue is the main color of the image.
    BLUE = ProtoImageSpec.ImageColor.IMAGE_COLOR_BLUE
    #: Violet is the main color of the image.
    VIOLET = ProtoImageSpec.ImageColor.IMAGE_COLOR_VIOLET
    #: White is the main color of the image.
    WHITE = ProtoImageSpec.ImageColor.IMAGE_COLOR_WHITE
    #: Black is the main color of the image.
    BLACK = ProtoImageSpec.ImageColor.IMAGE_COLOR_BLACK
