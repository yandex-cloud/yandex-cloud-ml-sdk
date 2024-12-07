# pylint: disable=protected-access
from __future__ import annotations

from typing import TYPE_CHECKING

from get_annotations import get_annotations

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.function import BaseModelFunction

from .completions.function import AsyncCompletions, BaseCompletions, Completions
from .image_generation.function import AsyncImageGeneration, ImageGeneration
from .text_classifiers.function import AsyncTextClassifiers, BaseTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, TextEmbeddings

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseModels(BaseDomain):
    completions: BaseCompletions
    text_classifiers: BaseTextClassifiers

    def __init__(self, name: str, sdk: BaseSDK):
        super().__init__(name=name, sdk=sdk)
        self._init_functions()

    def _init_functions(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member_class in members.items():
            if not issubclass(member_class, BaseModelFunction):
                continue
            function = member_class(name=member_name, sdk=self._sdk, parent_resource=self)
            setattr(self, member_name, function)


class AsyncModels(BaseModels):
    completions: AsyncCompletions
    text_embeddings: AsyncTextEmbeddings
    text_classifiers: AsyncTextClassifiers
    image_generation: AsyncImageGeneration


class Models(BaseModels):
    completions: Completions
    text_embeddings: TextEmbeddings
    text_classifiers: TextClassifiers
    image_generation: ImageGeneration
