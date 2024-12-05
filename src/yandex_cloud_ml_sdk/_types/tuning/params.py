# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Generic, TypeVar, Union

from yandex.cloud.ai.tuning.v1.tuning_service_pb2 import (
    TextClassificationMulticlassParams, TextClassificationMultilabelParams, TextToTextCompletionTuningParams
)

from .optimizers import BaseOptimizer
from .schedulers import BaseScheduler
from .tuning_types import BaseTuningType

ProtoTuningParamsTypeT = TypeVar(
    'ProtoTuningParamsTypeT',
    bound=Union[
        TextToTextCompletionTuningParams,
        TextClassificationMulticlassParams,
        TextClassificationMultilabelParams
    ],
)


class BaseTuningParamProtoGeneric(Generic[ProtoTuningParamsTypeT]):
    # to avoid turning this field to dataclass field
    _proto_tuning_params_type: type[ProtoTuningParamsTypeT]
    _proto_tuning_argument_name: str


@dataclass(frozen=True)
class BaseTuningParams(BaseTuningParamProtoGeneric[ProtoTuningParamsTypeT]):
    tuning_type: BaseTuningType | None = None
    scheduler: BaseScheduler | None = None
    optimizer: BaseOptimizer | None = None

    def to_proto(self) -> ProtoTuningParamsTypeT:
        kwargs = asdict(self)
        for field in ('tuning_type', 'scheduler', 'optimizer'):
            del kwargs[field]

        if self.tuning_type:
            kwargs[self.tuning_type.field_name] = self.tuning_type.to_proto(
                self.tuning_type.proto_type
            )

        if self.scheduler:
            kwargs[self.scheduler.field_name] = self.scheduler.to_proto(
                self._proto_tuning_params_type.Scheduler
            )

        if self.optimizer:
            kwargs[self.optimizer.field_name] = self.optimizer.to_proto(
                self._proto_tuning_params_type.Optimizer
            )

        return self._proto_tuning_params_type(**kwargs)
