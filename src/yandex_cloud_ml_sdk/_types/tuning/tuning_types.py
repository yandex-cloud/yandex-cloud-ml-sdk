# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import ClassVar

from yandex.cloud.ai.tuning.v1.tuning_types_pb2 import TuningTypeLora, TuningTypePromptTune

from .parameter import BaseTuningParameter


class BaseTuningType(BaseTuningParameter):
    @property
    @abc.abstractmethod
    def field_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def proto_type(self) -> TuningTypeLora | TuningTypePromptTune:
        pass


@dataclass(frozen=True)
class TuningTypeLora(BaseTuningType):
    proto_type: ClassVar = TuningTypeLora
    field_name: ClassVar[str] = 'lora'

    rank: int | None = None
    alpha: float | None = None
    initialization: str | None = None
    type: str | None = None


@dataclass(frozen=True)
class TuningTypePromptTune(BaseTuningType):
    proto_type: ClassVar = TuningTypePromptTune
    field_name: ClassVar[str] = 'prompt_tune'

    virtual_tokens: int | None = None
