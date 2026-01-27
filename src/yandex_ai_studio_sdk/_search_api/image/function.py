# pylint: disable=redefined-builtin
from __future__ import annotations

from typing_extensions import override
from yandex_ai_studio_sdk._search_api.enums import (
    FamilyMode, FixTypoMode, ImageColor, ImageFormat, ImageOrientation, ImageSize, SearchType
)
from yandex_ai_studio_sdk._types.enum import EnumWithUnknownInput, UndefinedOrEnumWithUnknownInput
from yandex_ai_studio_sdk._types.function import BaseModelFunction
from yandex_ai_studio_sdk._types.misc import UNDEFINED, UndefinedOr
from yandex_ai_studio_sdk._utils.doc import doc_from

from .config import ImageSearchConfig
from .image import AsyncImageSearch, ImageSearch, ImageSearchTypeT


class BaseImageSearchFunction(BaseModelFunction[ImageSearchTypeT]):
    """Image search function for creating search object which provides
    methods for invoking image search.
    """

    @override
    # pylint: disable-next=too-many-locals
    def __call__(
        self,
        search_type: EnumWithUnknownInput[SearchType],
        *,
        family_mode: UndefinedOrEnumWithUnknownInput[FamilyMode] = UNDEFINED,
        fix_typo_mode: UndefinedOrEnumWithUnknownInput[FixTypoMode] = UNDEFINED,
        format: UndefinedOrEnumWithUnknownInput[ImageFormat] = UNDEFINED,
        size: UndefinedOrEnumWithUnknownInput[ImageSize] = UNDEFINED,
        orientation: UndefinedOrEnumWithUnknownInput[ImageOrientation] = UNDEFINED,
        color: UndefinedOrEnumWithUnknownInput[ImageColor] = UNDEFINED,
        site: UndefinedOr[str] = UNDEFINED,
        docs_on_page: UndefinedOr[int] = UNDEFINED,
        user_agent: UndefinedOr[str] = UNDEFINED,
    ) -> ImageSearchTypeT:
        """
        Creates image search object which provides methods for image search.

        To learn more about parameters and their formats and possible values,
        refer to
        `image search documentation <https://yandex.cloud/ru/docs/search-api/concepts/image-search#parameters>`_

        :param search_type: Search type.
        :param family_mode: Results filtering.
        :param fix_typo_mode: Search query typo correction setting.
        :param format: Searching for images in a particular format.
        :param size: Searching for images of a particular size.
        :param orientation: Searching for images with a particular orientation.
        :param color: Searching for images containing a particular color.
        :param site: Number of results per search result page.
        :param docs_on_page: Number of results per search result page.
        :param user_agent: String containing the User-Agent header.
            Use this parameter to have your search results optimized for a
            specific device and browser, including mobile search results.
        """
        config = ImageSearchConfig(
            search_type=SearchType._coerce(search_type)
        )
        search_api = self._model_type(sdk=self._sdk, uri='<search_api>', config=config)

        return search_api.configure(
            family_mode=family_mode,
            fix_typo_mode=fix_typo_mode,
            format=format,
            size=size,
            orientation=orientation,
            color=color,
            site=site,
            docs_on_page=docs_on_page,
            user_agent=user_agent,
        )


@doc_from(BaseImageSearchFunction)
class ImageSearchFunction(BaseImageSearchFunction[ImageSearch]):
    _model_type = ImageSearch


@doc_from(BaseImageSearchFunction)
class AsyncImageSearchFunction(BaseImageSearchFunction[AsyncImageSearch]):
    _model_type = AsyncImageSearch
