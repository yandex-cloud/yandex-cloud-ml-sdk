# pylint: disable=abstract-method,wrong-import-position
from __future__ import annotations

from typing import Generic, TypeVar

from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel as PydanticModel
from pydantic import ConfigDict

from yandex_cloud_ml_sdk._types.model import BaseModel

#: Type variable for BaseModel subclasses used in generic type annotations.
ModelTypeT = TypeVar('ModelTypeT', bound=BaseModel)


class BaseYandexModel(PydanticModel, Generic[ModelTypeT]):
    """
    Class for models with Langchain integration.

    This class serves as a foundation for creating Langchain-compatible wrappers
    around models. It combines Pydantic's validation capabilities with generic typing support.

    :param ycmlsdk_model: The underlying model instance.
    :param timeout: The timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
    """
    ycmlsdk_model: ModelTypeT
    timeout: int = 60

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class BaseYandexLanguageModel(BaseYandexModel[ModelTypeT], BaseLanguageModel):
    """
    Class for Yandex language models compatible with Langchain.

    This class extends BaseYandexModel with Langchain's BaseLanguageModel
    interface, providing a complete foundation for implementing language
    models that can be used within the Langchain ecosystem.

    Inherits all parameters from BaseYandexModel.
    """

    @property
    def _llm_type(self):
        return 'yandex'
