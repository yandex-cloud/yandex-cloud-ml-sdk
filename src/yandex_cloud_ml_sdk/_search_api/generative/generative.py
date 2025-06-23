# pylint: disable=arguments-renamed,no-name-in-module
from __future__ import annotations

from typing import TypeVar

from typing_extensions import Self, override
from yandex.cloud.searchapi.v2.gen_search_service_pb2 import GenSearchRequest, GenSearchResponse
from yandex.cloud.searchapi.v2.gen_search_service_pb2_grpc import GenSearchServiceStub

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.model import ModelSyncMixin
from yandex_cloud_ml_sdk._types.string import SmartStringSequence
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import GenerativeSearchConfig, SmartFilterSequence, format_to_proto
from .message import MessageInputType, messages_to_proto
from .result import GenerativeSearchResult

logger = get_logger(__name__)


class BaseGenerativeSearch(ModelSyncMixin[GenerativeSearchConfig, GenerativeSearchResult]):
    """Generative search class which provides concrete methods for working with Search API
    and incapsulates search setting.
    """

    _config_type = GenerativeSearchConfig
    _result_type = GenerativeSearchResult

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        site: UndefinedOr[SmartStringSequence] | None = UNDEFINED,
        host: UndefinedOr[SmartStringSequence] | None = UNDEFINED,
        url: UndefinedOr[SmartStringSequence] | None = UNDEFINED,
        fix_misspell: UndefinedOr[bool] | None = UNDEFINED,
        enable_nrfm_docs: UndefinedOr[bool] | None = UNDEFINED,
        search_filters: UndefinedOr[SmartFilterSequence] | None = UNDEFINED
    ) -> Self:
        """
        Returns the new object with config fields overrode by passed values.

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

        return super().configure(
            site=site,
            host=host,
            url=url,
            fix_misspell=fix_misspell,
            enable_nrfm_docs=enable_nrfm_docs,
            search_filters=search_filters
        )

    @override
    def __repr__(self) -> str:
        # Generative Search doesn't have an uri value, but I'm lazy to refactor
        # to make an additional ancestor without an uri
        return f'{self.__class__.__name__}(config={self._config})'

    @override
    async def _run(self, request: MessageInputType, *, timeout: float = 60) -> GenerativeSearchResult:
        """Run a search query with given ``request`` and search settings of this generative search
        object.

        To change initial search settings use ``.configure`` method:

        >>> search = sdk.search_api.generative(site="site")
        >>> search = search.configure(site="other_site")

        :param request: search request, which could be either standalone request (message) or
            a list of messages, which represents a context of conversation with a model.

            Also message could be one of the data formats:

            * ``"string"`` -- in case of string input message will be passed to a model with a ``role="user"``;

            * ``{"text": "text", "role": "user"}`` -- in case of dict input, it will be passed
              with corresponding ``"text"`` and ``"role"`` dict keys;

            * ``MessageObject`` -- you could also pass any object which have a
              ``text: str`` and ``role: str`` attributes, allowing to reuse various
              result object, for example object you getting from compltions model run
              or result object from generative search itself;

            * ``["string"/dict/object]`` -- list or any other sequence of any above described
              formats.

        :param timeout: timeout, or the maximum time to wait for the request to complete in seconds.

        """
        self.config._validate_run()
        messages = messages_to_proto(request)

        kwargs = self._config._asdict()
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        logger.debug('Going to execute query `%r` with config %r', request, kwargs)

        # NB: we know that one and only one of this options are not-None here
        # because of config._validate_configure() and config._validate_run()
        if self.config.host:
            kwargs['host'] = GenSearchRequest.HostOption(host=self.config.host)
        elif self.config.site:
            kwargs['site'] = GenSearchRequest.SiteOption(site=self.config.site)
        elif self.config.url:
            kwargs['url'] = GenSearchRequest.UrlOption(url=self.config.url)

        search_filters: list[GenSearchRequest.SearchFilter] | None = None
        if raw_search_filters := kwargs.pop('search_filters', None):
            search_filters = []
            for filter_ in raw_search_filters:
                if format_ := filter_.get('format'):
                    filter_['format'] = format_to_proto(format_)
                search_filters.append(
                    GenSearchRequest.SearchFilter(**filter_)
                )
        kwargs['search_filters'] = search_filters

        req = GenSearchRequest(
            messages=messages,
            folder_id=self._sdk._folder_id,
            **kwargs,
        )

        async with self._client.get_service_stub(GenSearchServiceStub, timeout=timeout) as stub:
            async for response in self._client.call_service_stream(
                stub.Search,
                req,
                timeout=timeout,
                expected_type=GenSearchResponse
            ):
                return GenerativeSearchResult._from_proto(proto=response, sdk=self._sdk)

        raise RuntimeError("call returned less then one result")


@doc_from(BaseGenerativeSearch)
class AsyncGenerativeSearch(BaseGenerativeSearch):
    @doc_from(BaseGenerativeSearch._run)
    async def run(self, request: MessageInputType, *, timeout: float = 60) -> GenerativeSearchResult:
        return await self._run(request=request, timeout=timeout)


@doc_from(BaseGenerativeSearch)
class GenerativeSearch(BaseGenerativeSearch):
    __run = run_sync(BaseGenerativeSearch._run)

    @doc_from(BaseGenerativeSearch._run)
    def run(self, request: MessageInputType, *, timeout: float = 60) -> GenerativeSearchResult:
        return self.__run(request=request, timeout=timeout)


GenerativeSearchTypeT = TypeVar('GenerativeSearchTypeT', bound=BaseGenerativeSearch)
