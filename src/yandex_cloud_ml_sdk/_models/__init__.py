from __future__ import annotations

from typing import TYPE_CHECKING

from get_annotations import get_annotations

from yandex_cloud_ml_sdk._types.function import BaseFunction
from yandex_cloud_ml_sdk._types.resource import BaseResource

from .completions.function import AsyncCompletions, Completions
from .text_classifiers.function import AsyncTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, TextEmbeddings

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


class BaseModels(BaseResource):
    def __init__(self, name: str, sdk: BaseSDK):
        super().__init__(name=name, sdk=sdk)
        self._init_functions()

    def _init_functions(self) -> None:
        members: dict[str, type] = get_annotations(self.__class__, eval_str=True)
        for member_name, member_class in members.items():
            if issubclass(member_class, BaseFunction):
                function = member_class(name=member_name, sdk=self._sdk)
                setattr(self, member_name, function)


class AsyncModels(BaseModels):
    completions: AsyncCompletions
    text_embeddings: AsyncTextEmbeddings
    text_classifiers: AsyncTextClassifiers


class Models(BaseModels):
    completions: Completions
    text_embeddings: TextEmbeddings
    text_classifiers: TextClassifiers
