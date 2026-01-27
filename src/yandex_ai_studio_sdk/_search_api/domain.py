from __future__ import annotations

from yandex_ai_studio_sdk._types.domain import DomainWithFunctions
from yandex_ai_studio_sdk._utils.doc import doc_from

from .by_image.function import AsyncByImageSearchFunction, BaseByImageSearchFunction, ByImageSearchFunction
from .generative.function import AsyncGenerativeSearchFunction, BaseGenerativeSearchFunction, GenerativeSearchFunction
from .image.function import AsyncImageSearchFunction, BaseImageSearchFunction, ImageSearchFunction
from .web.function import AsyncWebSearchFunction, BaseWebSearchFunction, WebSearchFunction


class BaseSearchAPIDomain(DomainWithFunctions):
    """
    Domain for working with `Yandex Search API <https://yandex.cloud/docs/search-api>`_ services.
    """

    #: API for `generative response <https://yandex.cloud/docs/search-api/concepts/generative-response>`_ service
    generative: BaseGenerativeSearchFunction
    #: API for `web search <https://yandex.cloud/ru/docs/search-api/concepts/web-search>`_ service
    web: BaseWebSearchFunction
    #: API for `text image search <https://yandex.cloud/ru/docs/search-api/concepts/image-search#search-by-text-query>`_ service
    image: BaseImageSearchFunction
    #: API for `search by image <https://yandex.cloud/ru/docs/search-api/concepts/image-search#search-by-image>`_ service
    by_image: BaseByImageSearchFunction


@doc_from(BaseSearchAPIDomain)
class AsyncSearchAPIDomain(BaseSearchAPIDomain):
    generative: AsyncGenerativeSearchFunction
    web: AsyncWebSearchFunction
    image: AsyncImageSearchFunction
    by_image: AsyncByImageSearchFunction


@doc_from(BaseSearchAPIDomain)
class SearchAPIDomain(BaseSearchAPIDomain):
    generative: GenerativeSearchFunction
    web: WebSearchFunction
    image: ImageSearchFunction
    by_image: ByImageSearchFunction
