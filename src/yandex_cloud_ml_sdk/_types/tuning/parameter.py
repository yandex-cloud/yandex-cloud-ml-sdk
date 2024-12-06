from __future__ import annotations

import abc
from dataclasses import asdict, dataclass

from yandex_cloud_ml_sdk._types.proto import ProtoMessageTypeT


@dataclass(frozen=True)
class BaseTuningParameter(abc.ABC):
    @property
    @abc.abstractmethod
    def field_name(self) -> str:
        pass

    def to_proto(self, proto_type: type[ProtoMessageTypeT]) -> ProtoMessageTypeT:
        return proto_type(
            **asdict(self)
        )
