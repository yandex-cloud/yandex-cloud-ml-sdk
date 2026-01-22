# pylint: disable=redefined-builtin
from __future__ import annotations

from typing_extensions import override

from yandex_ai_studio_sdk._search_api.enums import FamilyMode
from yandex_ai_studio_sdk._types.enum import UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._utils.doc import doc_from

from .by_image import AsyncByImageSearch, ByImageSearch, ByImageSearchTypeT


class BaseByImageSearchFunction(BaseModelFunction[ByImageSearchTypeT]):
    """ByImage search function for creating search object which provides
    methods for invoking by_image search.
    """

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
        *,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] = UNDEFINED,
        site: UndefinedOr[str] = UNDEFINED,
    ) -> ByImageSearchTypeT:
        """
        Creates by_image search object which provides methods for search by image.

        To learn more about parameters and their formats and possible values,
        refer to
        `search by image documentation <https://yandex.cloud/ru/docs/search-api/concepts/image-search#request-body-by-pic>`_

        :param family_mode: Results filtering.
        :param site: Restricts the search to the specific website.
        """
        search_api = self._model_type(sdk=self._sdk, uri='<search_api>')

        return search_api.configure(
            family_mode=family_mode,
            site=site,
        )


@doc_from(BaseByImageSearchFunction)
class ByImageSearchFunction(BaseByImageSearchFunction[ByImageSearch]):
    _model_type = ByImageSearch


@doc_from(BaseByImageSearchFunction)
class AsyncByImageSearchFunction(BaseByImageSearchFunction[AsyncByImageSearch]):
    _model_type = AsyncByImageSearch
