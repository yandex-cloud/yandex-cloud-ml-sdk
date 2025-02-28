from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from typing_extensions import Self

from .proto import ProtoMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

@runtime_checkable
class BaseResult(Protocol):
    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:
        raise NotImplementedError()
