# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .completions.function import AsyncCompletions, BaseCompletions, Completions
from .image_generation.function import AsyncImageGeneration, BaseImageGeneration, ImageGeneration
from .text_classifiers.function import AsyncTextClassifiers, BaseTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, BaseTextEmbeddings, TextEmbeddings


class BaseModels(DomainWithFunctions):
    """Domain for working with `Yandex Foundation Models <https://yandex.cloud/ru/services/foundation-models>`."""
    completions: BaseCompletions
    text_classifiers: BaseTextClassifiers
    image_generation: BaseImageGeneration
    text_embeddings: BaseTextEmbeddings


@doc_from(BaseModels)
class AsyncModels(BaseModels):
    completions: AsyncCompletions
    text_embeddings: AsyncTextEmbeddings
    text_classifiers: AsyncTextClassifiers
    image_generation: AsyncImageGeneration


@doc_from(BaseModels)
class Models(BaseModels):
    completions: Completions
    text_embeddings: TextEmbeddings
    text_classifiers: TextClassifiers
    image_generation: ImageGeneration
