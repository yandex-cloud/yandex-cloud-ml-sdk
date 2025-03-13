# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from functools import cached_property

from yandex_cloud_ml_sdk._search_indexes.search_index import BaseSearchIndex
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.schemas import ParametersType, schema_from_parameters
from yandex_cloud_ml_sdk._utils.coerce import ResourceType, coerce_resource_ids

from .tool import FunctionTool, SearchIndexTool


class Tools(BaseDomain):
    @cached_property
    def function(self) -> FunctionTools:
        return FunctionTools(
            name='tools.function',
            sdk=self._sdk
        )

    def search_index(
        self,
        indexes: ResourceType[BaseSearchIndex],
        *,
        max_num_results: UndefinedOr[int] = UNDEFINED,
    ):
        index_ids = coerce_resource_ids(indexes, BaseSearchIndex)
        max_num_results_ = get_defined_value(max_num_results, None)
        return SearchIndexTool(
            search_index_ids=tuple(index_ids),
            max_num_results=max_num_results_
        )


class FunctionTools(BaseDomain):
    def __call__(
        self,
        *,
        name: str,
        description: UndefinedOr[str] = UNDEFINED,
        parameters: ParametersType,
    ) -> FunctionTool:
        schema = schema_from_parameters(parameters)
        return FunctionTool(
            parameters=schema,
            name=name,
            description=get_defined_value(description, None)
        )
