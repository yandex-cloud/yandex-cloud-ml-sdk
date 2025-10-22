from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .generative.function import AsyncGenerativeSearchFunction, BaseGenerativeSearchFunction, GenerativeSearchFunction
from .web.function import AsyncWebSearchFunction, BaseWebSearchFunction, WebSearchFunction


class BaseSearchAPIDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex Search API <https://yandex.cloud/docs/search-api>`_ services.
    """

    #: API for `generative response <https://yandex.cloud/docs/search-api/concepts/generative-response>`_ service
    generative: BaseGenerativeSearchFunction
    #: API for `web search <https://yandex.cloud/ru/docs/search-api/concepts/web-search>`_ service
    web: BaseWebSearchFunction


@doc_from(BaseSearchAPIDomain)
class AsyncSearchAPIDomain(BaseSearchAPIDomain):
    generative: AsyncGenerativeSearchFunction
    web: AsyncWebSearchFunction


@doc_from(BaseSearchAPIDomain)
class SearchAPIDomain(BaseSearchAPIDomain):
    generative: GenerativeSearchFunction
    web: WebSearchFunction
