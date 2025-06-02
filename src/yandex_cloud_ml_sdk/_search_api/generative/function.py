from __future__ import annotations

from typing_extensions import override

from yandex_cloud_ml_sdk._types.function import BaseModelFunction
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_cloud_ml_sdk._types.string import SmartStringSequence

from .config import AVAILABLE_FORMATS, SmartFilterSequence
from .generative import AsyncGenerativeSearch, GenerativeSearch, GenerativeSearchTypeT


class BaseGenerativeSearchFunction(BaseModelFunction[GenerativeSearchTypeT]):
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


class GenerativeSearchFunction(BaseGenerativeSearchFunction[GenerativeSearch]):
    _model_type = GenerativeSearch


class AsyncGenerativeSearchFunction(BaseGenerativeSearchFunction[AsyncGenerativeSearch]):
    _model_type = AsyncGenerativeSearch
