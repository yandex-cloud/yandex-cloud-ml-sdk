# pylint: disable=abstract-method
from __future__ import annotations

from typing import Generic, TypeVar

import langchain_core
from langchain_core.language_models.base import BaseLanguageModel

from yandex_cloud_ml_sdk._types.model import BaseModel

ModelTypeT = TypeVar('ModelTypeT', bound=BaseModel)

NEEDS_REBUILD = False

if langchain_core.__version__.startswith('0.2'):
    from langchain_core.load import Serializable
    from langchain_core.pydantic_v1 import BaseModel as LangchainModel

    class BaseYandexModel(LangchainModel, Generic[ModelTypeT]):
        ycmlsdk_model: ModelTypeT
        timeout: int = 60

        class Config(Serializable.Config):
            arbitrary_types_allowed = True

else:
    from pydantic import BaseModel as LangchainModel
    from pydantic import ConfigDict

    NEEDS_REBUILD = True

    class BaseYandexModel(LangchainModel, Generic[ModelTypeT]):
        ycmlsdk_model: ModelTypeT
        timeout: int = 60

        model_config = ConfigDict(
            arbitrary_types_allowed=True
        )


class BaseYandexLanguageModel(BaseYandexModel[ModelTypeT], BaseLanguageModel):
    @property
    def _llm_type(self):
        return 'yandex'
