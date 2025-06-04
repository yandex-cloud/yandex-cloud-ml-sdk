# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .completions.function import AsyncCompletions, BaseCompletions, Completions
from .image_generation.function import AsyncImageGeneration, ImageGeneration
from .text_classifiers.function import AsyncTextClassifiers, BaseTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, TextEmbeddings


class BaseModels(DomainWithFunctions):
    """
    Domain for working with `Yandex Foundation Models <https://yandex.cloud/ru/services/foundation-models>`.
    """
    #: Completions doc
    completions: BaseCompletions
    #: Text_classifiers doc
    text_classifiers: BaseTextClassifiers
    #: Image_generation doc 
    image_generation: BaseImageGeneration
    #: Text_embeddings doc
    text_embeddings: BaseTextEmbeddings


@doc_from(BaseModels)
@doc_from(BaseModels.image_generation)
@doc_from(BaseModels.text_embeddings)
class AsyncModels(BaseModels):
    completions: AsyncCompletions
    text_embeddings: AsyncTextEmbeddings
    text_classifiers: AsyncTextClassifiers
    image_generation: AsyncImageGeneration


@doc_from(BaseModels)
@doc_from(BaseModels.image_generation)
@doc_from(BaseModels.text_embeddings)
class Models(BaseModels):
    completions: Completions
    text_embeddings: TextEmbeddings
    text_classifiers: TextClassifiers
    image_generation: ImageGeneration
