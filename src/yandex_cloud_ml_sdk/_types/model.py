from __future__ import annotations

import abc
from dataclasses import replace
from typing import TYPE_CHECKING, AsyncIterator, Generic, TypeVar

from yandex_cloud_ml_sdk._tuning.tuning_task import TuningTaskTypeT

from .misc import Undefined, UndefinedOr, get_defined_value
from .model_config import BaseModelConfig
from .operation import OperationTypeT
from .result import BaseResult, ProtoMessage
from .tuning.datasets import TuningDatasetsType
from .tuning.params import BaseTuningParams

if TYPE_CHECKING:
    from typing_extensions import Self

    from yandex_cloud_ml_sdk._sdk import BaseSDK


ConfigTypeT = TypeVar('ConfigTypeT', bound=BaseModelConfig)
ResultTypeT = TypeVar('ResultTypeT', bound=BaseResult)
TuningParamsTypeT = TypeVar('TuningParamsTypeT', bound=BaseTuningParams)


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
    _proto_result_type: type[ProtoMessage]

    @abc.abstractmethod
    async def _run_deferred(self, *args, **kwargs) -> OperationTypeT:
        pass

    # pylint: disable=unused-argument
    async def _attach_deferred(self, operation_id: str, timeout: float = 60) -> OperationTypeT:
        return self._operation_type(
            id=operation_id,
            sdk=self._sdk,
            result_type=self._result_type,
            proto_result_type=self._proto_result_type,
        )


class ModelTuneMixin(
    BaseModel[ConfigTypeT, ResultTypeT],
    Generic[ConfigTypeT, ResultTypeT, TuningParamsTypeT, TuningTaskTypeT]
):
    _tuning_params_type: type[TuningParamsTypeT]
    _tune_operation_type: type[TuningTaskTypeT]

    async def _tune(
        self,
        timeout: float = 60,
        poll_timeout: int = 72 * 60 * 60,
        poll_interval: float = 60,
        **kwargs,
    ) -> Self:
        operation = await self._tune_deferred(
            **kwargs,
            timeout=timeout,
        )
        # pylint: disable=protected-access
        result = await operation._wait(
            timeout=timeout,
            poll_timeout=poll_timeout,
            poll_interval=poll_interval,
        )
        return result

    async def _tune_deferred(
        self,
        train_datasets: TuningDatasetsType,
        validation_datasets: UndefinedOr[TuningDatasetsType],
        name: UndefinedOr[str],
        description: UndefinedOr[str],
        labels: UndefinedOr[dict[str, str]],
        timeout: float = 60,
        **kwargs,
    ) -> TuningTaskTypeT:
        clean_kwargs = {
            key: get_defined_value(value, None)
            for key, value in kwargs.items()
        }
        params = self._tuning_params_type(**clean_kwargs)

        # pylint: disable=protected-access
        return await self._sdk.tuning._create_deferred(
            model_uri=self._uri,
            result_type=type(self),
            train_datasets=train_datasets,
            validation_datasets=validation_datasets,
            tuning_params=params,
            name=name,
            description=description,
            labels=labels,
            timeout=timeout
        )

    # pylint: disable=unused-argument
    async def _attach_tune_deferred(self, task_id: str, *, timeout: float = 60) -> TuningTaskTypeT:
        # TODO: it will break after operation will go out from cache (two weeks?)
        # we need to check, if it exists first, and create via task_id otherwise
        return self._tune_operation_type(
            operation_id=task_id,
            task_id=None,
            sdk=self._sdk,
            result_type=type(self)
        )
