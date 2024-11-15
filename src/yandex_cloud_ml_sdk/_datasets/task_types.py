from __future__ import annotations

from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .domain import AsyncDatasets, Datasets


class KnownTaskType(StrEnum):
    TextToTextGeneration = 'TextToTextGeneration'
    TextEmbeddings = 'TextEmbeddings'
    TextClassificationMultilabel = 'TextClassificationMultilabel'
    TextClassificationMulticlass = 'TextClassificationMulticlass'
    SpeechToTextGeneration = 'SpeechToTextGeneration'
    TextToSpeechGeneration = 'TextToSpeechGeneration'
    TextToImageGeneration = 'TextToImageGeneration'


class TaskTypeProxy:
    def __init__(self, task_type: KnownTaskType):
        self._task_type = task_type
        self._wrapper = None

    def __get__(self, obj: Datasets | AsyncDatasets | None, owner=None):
        if obj is None:
            return self

        if self._wrapper is None:
            self._wrapper = DatasetsWrapper(
                task_type=self._task_type,
                domain=obj
            )

        return self._wrapper


class DatasetsWrapper:
    def __init__(self, task_type: str, domain: Datasets | AsyncDatasets):
        self._task_type = task_type
        self._domain = domain

    @property
    def create(self):
        return partial(self._domain.create, task_type=self._task_type)

    @property
    def list_upload_formats(self):
        return partial(self._domain.list_upload_formats, task_type=self._task_type)
