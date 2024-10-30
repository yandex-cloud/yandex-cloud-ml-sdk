from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar

from google.protobuf.message import Message
from typing_extensions import Self

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

ProtoResultTypeT = TypeVar('ProtoResultTypeT', bound=Message)
T = TypeVar('T', bound='BaseResult')


class BaseResult(abc.ABC, Generic[ProtoResultTypeT]):
    _proto_result_type: type[ProtoResultTypeT]

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls: type[Self], proto: ProtoResultTypeT, sdk: BaseSDK) -> Self:
        raise NotImplementedError()
