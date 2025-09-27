from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypedDict, Union, cast

from typing_extensions import Self, TypeAlias, override
# pylint: disable=no-name-in-module
from yandex.cloud.searchapi.v2.gen_search_service_pb2 import GenSearchRequest

from yandex_cloud_ml_sdk._types.model_config import BaseModelConfig
from yandex_cloud_ml_sdk._types.string import SmartStringSequence, coerce_string_sequence
from yandex_cloud_ml_sdk._utils.coerce import coerce_tuple


class DateFilterType(TypedDict):
    """Date filter dict type for generative search.

    Example:

    >>> filter_ = {'date': '>20240125'}
    """

    date: str


class FormatFilterType(TypedDict):
    """Format filter dict type for generative search.

    Example:

    >>> filter_ = {'format': 'xlsx'}
    """

    format: str


class LangFilterType(TypedDict):
    """Language filter dict type for generative search.

    Example:

    >>> filter_ = {'lang': 'ru'}
    """

    lang: str

#: Generative search filter type which describes dict formats eligible to use with generative search API.
FilterType: TypeAlias = Union[DateFilterType, FormatFilterType, LangFilterType]
SmartFilterSequence: TypeAlias = Union[Sequence[FilterType], FilterType]

AVAILABLE_FORMATS = tuple(
    format.lower().removeprefix('doc_format_')
    for format, number in GenSearchRequest.SearchFilter.DocFormat.items()
    if format != 'DOC_FORMAT_UNSPECIFIED'
)
AVAILABLE_FORMATS_INPUTS = (
    set(AVAILABLE_FORMATS) |
    {'doc_format_' + format for format in AVAILABLE_FORMATS}
)


@dataclass(frozen=True)
class GenerativeSearchConfig(BaseModelConfig):
    #: Parameter for limiting search to specific location or list of sites.
    site: tuple[str, ...] | None = None
    #: Parameter for limiting search to specific location or list of hosts.
    host: tuple[str, ...] | None = None
    #: Parameter for limiting search to specific location or list of urls.
    url: tuple[str, ...] | None = None

    #: tells to backend to fix or not to fix misspels in queries.
    fix_misspell: bool | None = None
    #: tells to backend to include or not to include pages,
    #: which are not available via direct clicks from given sites/hosts/urls
    #: to search result.
    enable_nrfm_docs: bool | None = None
    #: allows to limit search results with additional filters.
    search_filters: tuple[FilterType, ...] | None = None

    @property
    def _url_score(self) -> int:
        return bool(self.site) + bool(self.host) + bool(self.url)

    @override
    def _validate_configure(self) -> None:
        if self._url_score > 1:
            raise ValueError('GenerativeSearch fields site, host and url are mutually exclusive')

        for filter_ in self.search_filters or ():
            if (
                not isinstance(filter_, dict)
                or len(filter_) != 1
                or list(filter_)[0] not in ('format', 'lang', 'date')
            ):
                raise ValueError(
                    "Filter must be a dict with one and only one key from a list 'format', 'lang', 'date'"
                )

            if format_ := filter_.get('format'):
                format_ = cast(str, format_)
                if format_.lower() not in AVAILABLE_FORMATS_INPUTS:
                    raise ValueError(f"Unknown format '{format_}', use one of {AVAILABLE_FORMATS}")

    @override
    def _validate_run(self) -> None:
        if not self._url_score:
            raise ValueError('GenerativeSearch must have one of the site, host or url fields set')

    @override
    def _replace(self, **kwargs: dict) -> Self:
        for field in ('site', 'host', 'url'):
            if field not in kwargs:
                continue

            value: SmartStringSequence | None = kwargs.get(field)  # type: ignore[assignment]
            if value:
                kwargs[field] = coerce_string_sequence(value)  # type: ignore[assignment]

        if 'search_filters' in kwargs:
            search_filters: SmartFilterSequence | None = kwargs.get('search_filters')  # type: ignore[arg-type,assignment]
            if search_filters:
                kwargs['search_filters'] = coerce_tuple(search_filters, dict)  # type: ignore[arg-type,assignment]

        return super()._replace(**kwargs)
