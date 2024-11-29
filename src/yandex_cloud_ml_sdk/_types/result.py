from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from google.protobuf.message import Message as ProtoMessage
from typing_extensions import Self

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

ProtoResultTypeT = TypeVar('ProtoResultTypeT', bound=ProtoMessage)
T = TypeVar('T', bound='BaseResult')


class BaseResult(Protocol):
    @classmethod
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:
        raise NotImplementedError()
