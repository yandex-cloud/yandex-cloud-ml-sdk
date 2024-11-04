# pylint: disable=abstract-method,wrong-import-position
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    raise NotImplementedError("Langchain integration doesn't supported for python<3.9")

from typing import Generic, TypeVar

from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel as PydanticModel
from pydantic import ConfigDict

from yandex_cloud_ml_sdk._types.model import BaseModel

ModelTypeT = TypeVar('ModelTypeT', bound=BaseModel)


class BaseYandexModel(PydanticModel, Generic[ModelTypeT]):
    ycmlsdk_model: ModelTypeT
    timeout: int = 60

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class BaseYandexLanguageModel(BaseYandexModel[ModelTypeT], BaseLanguageModel):
    @property
    def _llm_type(self):
        return 'yandex'
