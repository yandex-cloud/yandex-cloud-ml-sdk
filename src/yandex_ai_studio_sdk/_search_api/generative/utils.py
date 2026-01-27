# pylint: disable=no-name-in-module
from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar, Union

from yandex.cloud.ai.assistants.v1.common_pb2 import GenSearchOptions
from yandex.cloud.searchapi.v2.gen_search_service_pb2 import GenSearchRequest

from .config import AVAILABLE_FORMATS, FilterType

ProtoFilterType = Union[GenSearchRequest.SearchFilter, GenSearchOptions.SearchFilter]

ProtoFilterTypeT = TypeVar(
    'ProtoFilterTypeT',
    GenSearchRequest.SearchFilter,
    GenSearchOptions.SearchFilter,
)


def filters_to_proto(
    filters: tuple[FilterType, ...] | None,
    proto_type: type[ProtoFilterTypeT]
) -> list[ProtoFilterTypeT] | None:
    if not filters:
        return None

    result = []
    for filter_ in filters:
        kwargs: dict = dict(filter_)

        if format_ := filter_.get('format', None):
            assert isinstance(format_, str)
            kwargs['format'] = format_to_proto(format_)

        proto_filter: ProtoFilterTypeT = proto_type(**kwargs)
        result.append(proto_filter)

    return result


def filter_from_proto(proto_filter: ProtoFilterType) -> FilterType:
    if proto_filter.HasField('date'):
        return {'date': proto_filter.date}

    if proto_filter.HasField('lang'):
        return {'lang': proto_filter.lang}

    if proto_filter.HasField('format'):
        return {'format': format_from_proto(proto_filter.format)}

    raise RuntimeError(f'filter {proto_filter} have no know fields')


def filters_from_proto(filters: Iterable[ProtoFilterType]) -> tuple[FilterType, ...]:
    return tuple(
        filter_from_proto(f) for f in filters
    )


def format_to_proto(format_: str) -> int:
    format_ = format_.lower()
    assert format_ in AVAILABLE_FORMATS
    if not format_.startswith('doc_format_'):
        format_ = f'doc_format_{format_}'

    format_ = format_.upper()
    return int(
        GenSearchRequest.SearchFilter.DocFormat.Value(format_)
    )


def format_from_proto(format_: int) -> str:
    raw: str = GenSearchRequest.SearchFilter.DocFormat.Name(format_)  # type: ignore[arg-type]
    return raw.removeprefix('DOC_FORMAT_').lower()
