from __future__ import annotations

import abc
from typing import Generic, TypeVar

from google.protobuf.message import Message
from typing_extensions import Self

ProtoResultTypeT = TypeVar('ProtoResultTypeT', bound=Message)
T = TypeVar('T', bound='BaseResult')


class BaseResult(abc.ABC, Generic[ProtoResultTypeT]):
    _proto_result_type: type[ProtoResultTypeT]

    @classmethod
    @abc.abstractmethod
    def _from_proto(cls: type[Self], message: ProtoResultTypeT) -> Self:
        raise NotImplementedError()
