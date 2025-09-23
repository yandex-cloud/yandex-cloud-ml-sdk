# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from yandex.cloud.ai.assistants.v1.common_pb2 import GenSearchOptions as ProtoGenSearchOptions
from yandex.cloud.ai.assistants.v1.common_pb2 import GenSearchTool as ProtoGenSearchTool

from yandex_cloud_ml_sdk._search_api.generative.config import GenerativeSearchConfig
from yandex_cloud_ml_sdk._search_api.generative.utils import filters_from_proto, filters_to_proto
from yandex_cloud_ml_sdk._tools.tool import BaseTool, ProtoAssistantsTool, ProtoToolTypeT
from yandex_cloud_ml_sdk._types.proto import SDKType


@dataclass(frozen=True)
class GenerativeSearchTool(BaseTool[ProtoGenSearchTool], GenerativeSearchConfig):
    """
    A generative search tool that can be called by LLMs/Assistants models.

    To learn more about generative search itself, refer to
    `generative search documentation <https://yandex.cloud/docs/search-api/concepts/generative-response#body>`_

    Objects of this class could be used in any place which requires :py:class:`~.BaseTool` instance,
    but not every place/feature supports all of the tool types.
    """

    # NB: description is mandatory but because of inheritance we can't declare it without default value
    #: Description of tool instance which also instructs model when to call it.
    description: str = ''

    # pylint: disable=unused-argument
    @classmethod
    def _from_proto(cls, *, proto: ProtoGenSearchTool, sdk: SDKType) -> GenerativeSearchTool:
        options = proto.options

        def coerce_options_tuple(
            field_name: Literal['site', 'url', 'host']
        ) -> tuple[str, ...] | None:
            if not options.HasField(field_name):
                return None

            if value := getattr(options, field_name):
                real_value = getattr(value, field_name)
                return tuple(real_value)

            return None

        return cls(
            description=proto.description,
            site=coerce_options_tuple('site'),
            url=coerce_options_tuple('url'),
            host=coerce_options_tuple('host'),
            enable_nrfm_docs=options.enable_nrfm_docs,
            search_filters=filters_from_proto(options.search_filters)
        )

    def _to_proto(self, proto_type: type[ProtoToolTypeT]) -> ProtoToolTypeT:
        assert issubclass(proto_type, ProtoAssistantsTool)
        assert self.description

        if self.fix_misspell:
            raise ValueError('fix_misspel option is not supported in gen search tool')

        kwargs: dict = {}
        if self.host:
            kwargs['host'] = ProtoGenSearchOptions.HostOption(host=self.host)
        if self.site:
            kwargs['site'] = ProtoGenSearchOptions.SiteOption(site=self.site)
        if self.url:
            kwargs['url'] = ProtoGenSearchOptions.UrlOption(url=self.url)

        assert bool(kwargs.get('host')) + bool(kwargs.get('site')) + bool(kwargs.get('url')) <= 1

        if self.enable_nrfm_docs:
            kwargs['enable_nrfm_docs'] = self.enable_nrfm_docs
        if self.search_filters:
            kwargs['search_filters'] = filters_to_proto(self.search_filters, ProtoGenSearchOptions.SearchFilter)

        options = ProtoGenSearchOptions(
            **kwargs
        )

        return ProtoAssistantsTool(
            gen_search=ProtoGenSearchTool(
                description=self.description or '',
                options=options
            )
        )
