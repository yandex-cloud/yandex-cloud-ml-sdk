# pylint: disable=no-name-in-module
from __future__ import annotations

import abc
from functools import cached_property
from typing import Generic, TypeVar

from google.protobuf.message import Message
from typing_extensions import TypeAlias
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2 import BatchCompletionMetadata
from yandex.cloud.ai.foundation_models.v1.text_generation.text_generation_service_pb2_grpc import (
    TextGenerationBatchServiceStub
)

from yandex_cloud_ml_sdk._types.model import BaseModel, ConfigTypeT, ResultTypeT
# from yandex_cloud_ml_sdk._utils.doc import doc_from

from .domain import AsyncBatchSubdomain, BatchSubdomain, BatchSubdomainTypeT

#: Type alias for batch service stub used in batch processing operations
BatchStubType: TypeAlias = TextGenerationBatchServiceStub

#: Type alias for batch completion metadata returned by batch operations
BatchMetadataType: TypeAlias = BatchCompletionMetadata


class BaseModelBatchMixin(
    BaseModel[ConfigTypeT, ResultTypeT],
    Generic[ConfigTypeT, ResultTypeT, BatchSubdomainTypeT],
    metaclass=abc.ABCMeta,
):
    """
    Mixin class for models that support batch processing operations.

    This abstract base class provides the core functionality for models that need to support
    batch processing capabilities. It defines the interface for creating batch requests,
    accessing batch service stubs, and managing batch metadata.

    :param ConfigTypeT: Type parameter for model configuration
    :param ResultTypeT: Type parameter for model results
    :param BatchSubdomainTypeT: Type parameter for batch subdomain implementation
    """
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
    def _batch_proto_metadata_type(self) -> type[BatchMetadataType]:
        pass

    @cached_property
    def batch(self) -> BatchSubdomainTypeT:
        """
        Get the batch subdomain instance for this model.

        This property provides access to batch processing functionality through
        a cached subdomain instance. The instance is created lazily on first access.
        """
        return self._batch_impl(model=self, sdk=self._sdk)


# pylint: disable=abstract-method
# @doc_from(BaseModelBatchMixin)
class AsyncModelBatchMixin(
    BaseModelBatchMixin[ConfigTypeT, ResultTypeT, AsyncBatchSubdomain],
    Generic[ConfigTypeT, ResultTypeT],
):
    _batch_impl = AsyncBatchSubdomain


# pylint: disable=abstract-method
# @doc_from(BaseModelBatchMixin)
class ModelBatchMixin(
    BaseModelBatchMixin[ConfigTypeT, ResultTypeT, BatchSubdomain],
    Generic[ConfigTypeT, ResultTypeT],
):
    _batch_impl = BatchSubdomain


#: Type variable for models that inherit from BaseModelBatchMixin, used to ensure
#: type safety when working with batch-enabled models
ModelWithBatchTypeT = TypeVar('ModelWithBatchTypeT', bound=BaseModelBatchMixin)
