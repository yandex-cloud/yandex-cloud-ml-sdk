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
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .config import GenerativeSearchConfig, SmartFilterSequence, format_to_proto
from .message import MessageInputType, messages_to_proto
from .result import GenerativeSearchResult

logger = get_logger(__name__)


class BaseGenerativeSearch(ModelSyncMixin[GenerativeSearchConfig, GenerativeSearchResult]):
    _config_type = GenerativeSearchConfig
    _result_type = GenerativeSearchResult

    # pylint: disable=useless-parent-delegation,arguments-differ
    @override
    def configure(  # type: ignore[override]
        self,
        *,
        site: UndefinedOr[SmartStringSequence] = UNDEFINED,
        host: UndefinedOr[SmartStringSequence] = UNDEFINED,
        url: UndefinedOr[SmartStringSequence] = UNDEFINED,
        fix_misspell: UndefinedOr[bool] = UNDEFINED,
        enable_nrfm_docs: UndefinedOr[bool] = UNDEFINED,
        search_filters: UndefinedOr[SmartFilterSequence] = UNDEFINED
    ) -> Self:
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


class AsyncGenerativeSearch(BaseGenerativeSearch):
    async def run(self, request: MessageInputType, *, timeout: float = 60) -> GenerativeSearchResult:
        return await self._run(request=request, timeout=timeout)


class GenerativeSearch(BaseGenerativeSearch):
    __run = run_sync(BaseGenerativeSearch._run)

    def run(self, request: MessageInputType, *, timeout: float = 60) -> GenerativeSearchResult:
        return self.__run(request=request, timeout=timeout)


GenerativeSearchTypeT = TypeVar('GenerativeSearchTypeT', bound=BaseGenerativeSearch)
