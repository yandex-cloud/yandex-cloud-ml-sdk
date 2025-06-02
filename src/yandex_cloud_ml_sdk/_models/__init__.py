# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions

from .completions.function import AsyncCompletions, BaseCompletions, Completions
from .image_generation.function import AsyncImageGeneration, ImageGeneration
from .text_classifiers.function import AsyncTextClassifiers, BaseTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, TextEmbeddings


class BaseModels(DomainWithFunctions):
    completions: BaseCompletions
    text_classifiers: BaseTextClassifiers


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
