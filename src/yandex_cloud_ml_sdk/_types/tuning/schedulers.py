# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from dataclasses import asdict, dataclass
from typing import ClassVar, Union

from yandex.cloud.ai.tuning.v1.tuning_schedulers_pb2 import SchedulerConstant as ProtoSchedulerConstant
from yandex.cloud.ai.tuning.v1.tuning_schedulers_pb2 import SchedulerCosine as ProtoSchedulerCosine
from yandex.cloud.ai.tuning.v1.tuning_schedulers_pb2 import SchedulerLinear as ProtoSchedulerLinear

from .parameter import BaseTuningParameter, ProtoMessageTypeT

ProtoSchedulers = Union[ProtoSchedulerCosine, ProtoSchedulerLinear, ProtoSchedulerConstant]


@dataclass(frozen=True)
class BaseScheduler(BaseTuningParameter):
    field_name: ClassVar[str] = 'scheduler'
    warmup_ratio: float | None = None

    @property
    @abc.abstractmethod
    def proto_type(self) -> type[ProtoSchedulers]:
        pass

    @property
    @abc.abstractmethod
    def underlying_field_name(self) -> str:
        pass

    def to_proto(self, proto_type: type[ProtoMessageTypeT]) -> ProtoMessageTypeT:
        kwargs = asdict(self)
        kwargs.pop('warmup_ratio')

        return proto_type(
            warmup_ratio=self.warmup_ratio,
            **{self.underlying_field_name: self.proto_type(**kwargs)},
        )


@dataclass(frozen=True)
class SchedulerLinear(BaseScheduler):
    proto_type: ClassVar = ProtoSchedulerLinear
    underlying_field_name: ClassVar[str] = 'linear'
    min_lr: float | None = None


@dataclass(frozen=True)
class SchedulerConstant(BaseScheduler):
    proto_type: ClassVar = ProtoSchedulerConstant
    underlying_field_name: ClassVar[str] = 'constant'


@dataclass(frozen=True)
class SchedulerCosine(BaseScheduler):
    proto_type: ClassVar = ProtoSchedulerCosine
    underlying_field_name: ClassVar[str] = 'cosine'
    min_lr: float | None = None
