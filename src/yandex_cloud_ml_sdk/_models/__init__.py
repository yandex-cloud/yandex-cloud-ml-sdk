# pylint: disable=protected-access
from __future__ import annotations

from yandex_cloud_ml_sdk._types.domain import DomainWithFunctions
from yandex_cloud_ml_sdk._utils.doc import doc_from

from .completions.function import AsyncCompletions, BaseCompletions, Completions
from .image_generation.function import AsyncImageGeneration, ImageGeneration
from .text_classifiers.function import AsyncTextClassifiers, BaseTextClassifiers, TextClassifiers
from .text_embeddings.function import AsyncTextEmbeddings, TextEmbeddings


class BaseModels(DomainWithFunctions):
    """This class provides a structure for model-related functionalities,
    including completions and text classifiers. It initializes model
    functions based on defined annotations.
    """
    #: Completions doc
    completions: BaseCompletions
    #: Text_classifiers doc
    text_classifiers: BaseTextClassifiers


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
