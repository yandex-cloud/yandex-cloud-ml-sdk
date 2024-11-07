from __future__ import annotations

import abc
from dataclasses import replace
from typing import TYPE_CHECKING, AsyncIterator, Generic, TypeVar

from .misc import Undefined
from .model_config import BaseModelConfig
from .operation import OperationTypeT
from .result import BaseResult

if TYPE_CHECKING:
    from typing_extensions import Self

    from yandex_cloud_ml_sdk._sdk import BaseSDK


ConfigTypeT = TypeVar('ConfigTypeT', bound=BaseModelConfig)
ResultTypeT = TypeVar('ResultTypeT', bound=BaseResult)


class BaseModel(Generic[ConfigTypeT, ResultTypeT], metaclass=abc.ABCMeta):
    _config_type: type[ConfigTypeT]
    _result_type: type[ResultTypeT]

    def __init__(
        self,
        *,
        sdk: BaseSDK,
        uri: str,
        config: ConfigTypeT | None = None
    ):
        self._sdk = sdk
        self._uri = uri
        self._config = config if config else self._config_type()

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def config(self) -> ConfigTypeT:
        return self._config

    @property
    def _client(self):
        return self._sdk._client

    def configure(self, **kwargs) -> Self:
        kwargs = {
            k: v for k, v in kwargs.items()
            if not isinstance(v, Undefined)
        }

        return self.__class__(
            sdk=self._sdk,
            uri=self._uri,
            config=replace(self._config, **kwargs),
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(uri={self._uri}, config={self._config})'


class ModelSyncMixin(BaseModel[ConfigTypeT, ResultTypeT]):
    @abc.abstractmethod
    async def _run(self, *args, **kwargs) -> ResultTypeT:
        pass


class ModelSyncStreamMixin(BaseModel[ConfigTypeT, ResultTypeT]):
    @abc.abstractmethod
    async def _run_stream(self, *args, **kwargs) -> AsyncIterator[ResultTypeT]:
        raise NotImplementedError()

        # to make this method an iterator we need to write at least one yield
        yield BaseResult()  # pylint: disable=unreachable,abstract-class-instantiated


class ModelAsyncMixin(
    BaseModel[ConfigTypeT, ResultTypeT],
    Generic[ConfigTypeT, ResultTypeT, OperationTypeT]
):
    _operation_type: type[OperationTypeT]

    @abc.abstractmethod
    async def _run_deferred(self, *args, **kwargs) -> OperationTypeT:
        pass

    def attach_async(self, operation_id: str) -> OperationTypeT:
        return self._operation_type(
            id=operation_id,
            sdk=self._sdk,
            result_type=self._result_type,
        )
