from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.string import SmartStringSequence
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .config import AVAILABLE_FORMATS, SmartFilterSequence
from .generative import AsyncGenerativeSearch, GenerativeSearch, GenerativeSearchTypeT


class BaseGenerativeSearchFunction(BaseModelFunction[GenerativeSearchTypeT]):
    """Generative search function for creating search object which provides
    methods for invoking generative search.
    """

    @override
    def __call__(
        self,
        *,
        site: UndefinedOr[SmartStringSequence] = UNDEFINED,
        host: UndefinedOr[SmartStringSequence] = UNDEFINED,
        url: UndefinedOr[SmartStringSequence] = UNDEFINED,
        fix_misspell: UndefinedOr[bool] = UNDEFINED,
        enable_nrfm_docs: UndefinedOr[bool] = UNDEFINED,
        search_filters: UndefinedOr[SmartFilterSequence] = UNDEFINED
    ) -> GenerativeSearchTypeT:
        """
        Creates generative search object which provides methods for invoking generative search.

        To learn more about parameters and their formats and possible values,
        refer to
        `generative search documentation <https://yandex.cloud/docs/search-api/concepts/generative-response#body>`_

        NB: All of the ``site``, ``host``, ``url`` parameters are mutually exclusive
        and using one of them is mandatory.

        :param site: parameter for limiting search to specific location or list of sites.
        :param host: parameter for limiting search to specific location or list of hosts.
        :param url: parameter for limiting search to specific location or list of URLs.
        :param fix_misspell: tells to backend to fix or not to fix misspels in queries.
        :param enable_nrfm_docs: tells to backend to include or not to include pages,
            which are not available via direct clicks from given sites/hosts/urls
            to search result.
        :param search_filters: allows to limit search results with additional filters.

            >>> date_filter = {'date': '<20250101'}
            >>> format_filter = {'format': 'doc'}
            >>> lang_filter = {'lang': 'ru'}
            >>> search = sdk.search_api.generative(search_filters=[date_filter, format_filter, lang_filter])

        """
        search_api = self._model_type(sdk=self._sdk, uri='<search_api>')

        return search_api.configure(
            site=site,
            host=host,
            url=url,
            fix_misspell=fix_misspell,
            enable_nrfm_docs=enable_nrfm_docs,
            search_filters=search_filters
        )

    @property
    def available_formats(self):
        return AVAILABLE_FORMATS


@doc_from(BaseGenerativeSearchFunction)
class GenerativeSearchFunction(BaseGenerativeSearchFunction[GenerativeSearch]):
    _model_type = GenerativeSearch


@doc_from(BaseGenerativeSearchFunction)
class AsyncGenerativeSearchFunction(BaseGenerativeSearchFunction[AsyncGenerativeSearch]):
    _model_type = AsyncGenerativeSearch
