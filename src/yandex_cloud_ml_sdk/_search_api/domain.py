from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .generative.function import AsyncGenerativeSearchFunction, BaseGenerativeSearchFunction, GenerativeSearchFunction


class BaseSearchAPIDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex Search API <https://yandex.cloud/docs/search-api>` services.
    """

    #: API for `generative response <https://yandex.cloud/docs/search-api/concepts/generative-response>`_ service
    generative: BaseGenerativeSearchFunction


@doc_from(BaseSearchAPIDomain)
class AsyncSearchAPIDomain(BaseSearchAPIDomain):
    generative: AsyncGenerativeSearchFunction


@doc_from(BaseSearchAPIDomain)
class SearchAPIDomain(BaseSearchAPIDomain):
    generative: GenerativeSearchFunction
