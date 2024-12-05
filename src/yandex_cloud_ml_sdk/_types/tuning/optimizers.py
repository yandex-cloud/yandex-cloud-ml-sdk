# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import asdict, dataclass
from typing import ClassVar

from yandex.cloud.ai.tuning.v1.tuning_optimizers_pb2 import OptimizerAdamw as ProtoOptimizerAdamw

from .parameter import BaseTuningParameter, ProtoMessageTypeT

ProtoOptimizers = ProtoOptimizerAdamw


@dataclass(frozen=True)
class BaseOptimizer(BaseTuningParameter):
    field_name: ClassVar[str] = 'optimizer'

    @property
    @abc.abstractmethod
    def proto_type(self) -> type[ProtoOptimizerAdamw]:
        pass

    @property
    @abc.abstractmethod
    def underlying_field_name(self) -> str:
        pass

    def to_proto(self, proto_type: type[ProtoMessageTypeT]) -> ProtoMessageTypeT:
        kwargs = asdict(self)

        return proto_type(
            **{self.underlying_field_name: self.proto_type(**kwargs)},
        )


@dataclass(frozen=True)
class OptimizerAdamw(BaseOptimizer):
    proto_type: ClassVar = ProtoOptimizerAdamw
    underlying_field_name: ClassVar[str] = 'adamw'

    beta1: float | None = None
    beta2: float | None = None
    eps: float | None = None
    weight_decay: float | None = None
