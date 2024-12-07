# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import asdict, dataclass
from typing import Union, cast

from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    TextClassificationMulticlassParams, TextClassificationMultilabelParams, TextToTextCompletionTuningParams
)

from .optimizers import BaseOptimizer
from .schedulers import BaseScheduler
from .tuning_types import BaseTuningType

ProtoTuningParamsType = Union[
    TextToTextCompletionTuningParams,
    TextClassificationMulticlassParams,
    TextClassificationMultilabelParams
]


@dataclass(frozen=True)
class BaseTuningParams(abc.ABC):
    tuning_type: BaseTuningType | None = None
    scheduler: BaseScheduler | None = None
    optimizer: BaseOptimizer | None = None

    @property
    @abc.abstractmethod
    def _proto_tuning_params_type(self) -> type[ProtoTuningParamsType]:
        pass

    @property
    @abc.abstractmethod
    def _proto_tuning_argument_name(self) -> str:
        pass

    @property
    def _ignored_fields(self) -> tuple[str, ...]:
        return ('tuning_type', 'scheduler', 'optimizer')

    def to_proto(self) -> ProtoTuningParamsType:
        kwargs = asdict(self)
        for field in self._ignored_fields:
            del kwargs[field]

        if self.tuning_type:
            # NB: somewhy mypy expecting type[Never] as an argument here
            kwargs[self.tuning_type.field_name] = self.tuning_type.to_proto(
                self.tuning_type.proto_type  # type: ignore[arg-type]
            )

        if self.scheduler:
            kwargs[self.scheduler.field_name] = self.scheduler.to_proto(
                self._proto_tuning_params_type.Scheduler
            )

        if self.optimizer:
            kwargs[self.optimizer.field_name] = self.optimizer.to_proto(
                self._proto_tuning_params_type.Optimizer
            )

        return cast(ProtoTuningParamsType, self._proto_tuning_params_type(**kwargs))
