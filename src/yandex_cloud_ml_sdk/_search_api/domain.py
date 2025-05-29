from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions

from .generative.function import AsyncGenerativeSearchFunction, BaseGenerativeSearchFunction, GenerativeSearchFunction


class BaseSearchAPIDomain(DomainWithFunctions):
    generative: BaseGenerativeSearchFunction


class AsyncSearchAPIDomain(BaseSearchAPIDomain):
    generative: AsyncGenerativeSearchFunction


class SearchAPIDomain(BaseSearchAPIDomain):
    generative: GenerativeSearchFunction
