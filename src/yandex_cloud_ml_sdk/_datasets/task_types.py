# pylint: disable=invalid-name
from __future__ import annotations

from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from .domain import AsyncDatasets, Datasets


class KnownTaskType(str, Enum):
    """Enumeration of known task types."""
    #: task type for text-to-text generation
    TextToTextGeneration = 'TextToTextGeneration'
    #: task type for multilabel text classification
    TextClassificationMultilabel = 'TextClassificationMultilabel'
    #: task type for multiclass text classification
    TextClassificationMulticlass = 'TextClassificationMulticlass'
    #: task type for speech-to-text generation
    SpeechToTextGeneration = 'SpeechToTextGeneration'
    #: task type for text-to-speech generation
    TextToSpeechGeneration = 'TextToSpeechGeneration'
    #: task type for text-to-image generation
    TextToImageGeneration = 'TextToImageGeneration'
    #: task type for text embeddings in pairs
    TextEmbeddingsPair = 'TextEmbeddingsPair'
    #: task type for text embeddings in triplets
    TextEmbeddingsTriplet = 'TextEmbeddingsTriplet'

    #: request type for text-to-text generation
    TextToTextGenerationRequest = 'TextToTextGenerationRequest'
    #: request type for image-to-text generation
    ImageTextToTextGenerationRequest = 'ImageTextToTextGenerationRequest'


class TaskTypeProxy:
    """Proxy class for handling task types."""
    def __init__(self, task_type: KnownTaskType):
        self._task_type = task_type

    def _get_cache(self, obj: Datasets | AsyncDatasets) -> dict[str, DatasetsWrapper]:
        cache: dict[str, DatasetsWrapper] | None = cast(
            Optional[dict[str, DatasetsWrapper]], getattr(obj, '_task_proxy_cache', None)
        )
        if cache is None:
            cache = {}
            setattr(obj, '_task_proxy_cache', cache)

        return cache

    def __get__(self, obj: Datasets | AsyncDatasets | None, owner=None):
        if obj is None:
            return self

        cache = self._get_cache(obj)

        if not (wrapper := cache.get(self._task_type)):
            wrapper = cache[self._task_type] = DatasetsWrapper(
                task_type=self._task_type,
                domain=obj
            )

        return wrapper


class DatasetsWrapper:
    """Wrapper class for managing datasets associated with a task type."""
    def __init__(self, task_type: str, domain: Datasets | AsyncDatasets):
        self._task_type = task_type
        self._domain = domain

    @property
    def task_type(self) -> str:
        """A function for the task type managed by the wrapper."""
        return self._task_type

    @property
    def draft_from_path(self):
        """A function for drafting from a path based on the task type."""
        return partial(self._domain.draft_from_path, task_type=self._task_type)

    @property
    def list_upload_formats(self):
        """A function for listing upload formats based on the task type."""
        return partial(self._domain.list_upload_formats, task_type=self._task_type)

    @property
    def list_upload_schemas(self):
        """A function for listing upload schemas based on the task type."""
        return partial(self._domain.list_upload_schemas, task_type=self._task_type)

    @property
    def list(self):
        """A function for listing datasets based on the task type."""
        return partial(self._domain.list, task_type=self._task_type)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(task_type={self._task_type})'
