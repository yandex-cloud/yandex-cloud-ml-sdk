# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from functools import cached_property
from typing import Generic, TypeVar

from google.protobuf.message import Message
from typing_extensions import TypeAlias
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import (
    BatchCompletionMetadata, BatchCompletionResponse
)
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationBatchServiceStub
)

from yandex_cloud_ml_sdk._types.model import BaseModel, ConfigTypeT, ResultTypeT

from .domain import AsyncBatchSubdomain, BatchSubdomain, BatchSubdomainTypeT

BatchStubType: TypeAlias = TextGenerationBatchServiceStub
BatchResultType: TypeAlias = BatchCompletionResponse
BatchMetadataType: TypeAlias = BatchCompletionMetadata


class BaseModelBatchMixin(
    BaseModel[ConfigTypeT, ResultTypeT],
    Generic[ConfigTypeT, ResultTypeT, BatchSubdomainTypeT],
    metaclass=abc.ABCMeta,
):
    _batch_impl: type[BatchSubdomainTypeT]

    @abc.abstractmethod
    def _make_batch_request(self, dataset_id: str) -> Message:
        pass

    @property
    @abc.abstractmethod
    def _batch_service_stub(self) -> type[BatchStubType]:
        pass

    @property
    @abc.abstractmethod
    def _batch_proto_result_type(self) -> type[BatchResultType]:
        pass

    @property
    @abc.abstractmethod
    def _batch_proto_metadata_type(self) -> type[BatchMetadataType]:
        pass

    @cached_property
    def batch(self) -> BatchSubdomainTypeT:
        return self._batch_impl(model=self, sdk=self._sdk)


# pylint: disable=abstract-method
class AsyncModelBatchMixin(
    BaseModelBatchMixin[ConfigTypeT, ResultTypeT, AsyncBatchSubdomain],
    Generic[ConfigTypeT, ResultTypeT],
):
    _batch_impl = AsyncBatchSubdomain


# pylint: disable=abstract-method
class ModelBatchMixin(
    BaseModelBatchMixin[ConfigTypeT, ResultTypeT, BatchSubdomain],
    Generic[ConfigTypeT, ResultTypeT],
):
    _batch_impl = BatchSubdomain


ModelWithBatchTypeT = TypeVar('ModelWithBatchTypeT', bound=BaseModelBatchMixin)
