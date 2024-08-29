# pylint: disable=abstract-method
from __future__ import annotations

from typing import Generic, TypeVar

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.load import Serializable
from langchain_core.pydantic_v1 import BaseModel as LangchainModel

from yandex_cloud_ml_sdk._types.model import BaseModel

ModelTypeT = TypeVar('ModelTypeT', bound=BaseModel)


class BaseYandexModel(LangchainModel, Generic[ModelTypeT]):
    ycmlsdk_model: ModelTypeT
    timeout: int = 60

    class Config(Serializable.Config):
        arbitrary_types_allowed = True



class BaseYandexLanguageModel(BaseYandexModel[ModelTypeT], BaseLanguageModel):
    @property
    def _llm_type(self):
        return 'yandex'
