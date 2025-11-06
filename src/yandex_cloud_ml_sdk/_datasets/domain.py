# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

import warnings
from collections.abc import AsyncIterator, Iterable, Iterator
from typing import Generic, Union

from typing_extensions import TypeAlias
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import (
    CreateDatasetRequest, CreateDatasetResponse, DescribeDatasetRequest, DescribeDatasetResponse, ListDatasetsRequest,
    ListDatasetsResponse, ListUploadFormatsRequest, ListUploadFormatsResponse, ListUploadSchemasRequest,
    ListUploadSchemasResponse
)
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .dataset import AsyncDataset, Dataset, DatasetTypeT
from .draft import AsyncDatasetDraft, DatasetDraft, DatasetDraftT
from .schema import DatasetUploadSchema
from .status import DatasetStatus
from .task_types import KnownTaskType, TaskTypeProxy

logger = get_logger(__name__)

#: type alias for a single dataset status
SingleDatasetStatus: TypeAlias = Union[str, DatasetStatus]
#: type alias for input that can represent one or more dataset statuses
DatasetStatusInput: TypeAlias = Union[SingleDatasetStatus, Iterable[SingleDatasetStatus]]


class BaseDatasets(BaseDomain, Generic[DatasetTypeT, DatasetDraftT]):
    """This class provides methods to create and manage datasets of a specific type."""
    #: the implementation type for the dataset
    _dataset_impl: type[DatasetTypeT]
    #: the implementation type for the dataset draft
    _dataset_draft_impl: type[DatasetDraftT]

    #: a helper for autocompletion text-to-text generation tasks
    completions = TaskTypeProxy(KnownTaskType.TextToTextGeneration)
    #: a helper for autocompletion multilabel text classification tasks
    text_classifiers_multilabel = TaskTypeProxy(KnownTaskType.TextClassificationMultilabel)
    #: a helper for autocompletion multiclass text classification tasks
    text_classifiers_multiclass = TaskTypeProxy(KnownTaskType.TextClassificationMulticlass)
    #: a helper for autocompletion binary text classification tasks
    text_classifiers_binary = TaskTypeProxy(KnownTaskType.TextClassificationMultilabel)
    #: a helper for autocompletion pairwise text embeddings tasks
    text_embeddings_pair = TaskTypeProxy(KnownTaskType.TextEmbeddingsPair)
    #: a helper for autocompletion triplet text embeddings tasks
    text_embeddings_triplet = TaskTypeProxy(KnownTaskType.TextEmbeddingsTriplet)

    def draft_from_path(
        self,
        path: PathLike,
        *,
        task_type: UndefinedOr[str] = UNDEFINED,
        upload_format: UndefinedOr[str] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        metadata: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        allow_data_logging: UndefinedOr[bool] = UNDEFINED,
    ) -> DatasetDraftT:
        """Create a new dataset draft from a specified path.

        :param path: the path to the data file or directory.
        :param task_type: the type of task for the dataset.
        :param upload_format: the format in which the data should be uploaded.
        :param name: the name of the dataset.
        :param description: a description of the dataset.
        :param metadata: metadata associated with the dataset.
        :param labels: a set of labels for the dataset.
        :param allow_data_logging: a flag indicating if data logging is allowed.
        """
        logger.debug('Creating a new (local) dataset draft of type %s', task_type)
        return self._dataset_draft_impl(
            _domain=self,
            path=path,
            task_type=get_defined_value(task_type, None),
            upload_format=get_defined_value(upload_format, None),
            name=get_defined_value(name, None),
            description=get_defined_value(description, None),
            metadata=get_defined_value(metadata, None),
            labels=get_defined_value(labels, None),
            allow_data_logging=get_defined_value(allow_data_logging, None),
        )

    async def _create_impl(
        self,
        *,
        task_type: str,
        upload_format: str,
        name: str | None,
        description: str | None,
        metadata: str | None,
        labels: dict[str, str] | None,
        allow_data_logging: bool | None,
        timeout: float,
    ) -> DatasetTypeT:
        logger.debug('Creating a new (empty) dataset of type %s', task_type)

        request = CreateDatasetRequest(
            folder_id=self._folder_id,
            task_type=task_type,
            upload_format=upload_format,
            name=name or '',
            description=description or '',
            metadata=metadata or '',
            labels=labels or {},
            allow_data_log=allow_data_logging or False,
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=CreateDatasetResponse,
            )

        dataset = self._dataset_impl._from_proto(proto=response.dataset, sdk=self._sdk)
        logger.info('New (empty) dataset %s of type %s successfully created', dataset.id, task_type)
        return dataset

    async def _get(
        self,
        dataset_id: str,
        *,
        timeout: float = 60,
    ) -> DatasetTypeT:
        """Fetch a dataset from the server using its ID.

        :param dataset_id: the unique identifier of the dataset to fetch.
        :param timeout: the time to wait for the request.
            Defaults to 60 seconds.
        """
        logger.debug('Fetching dataset %s from server', dataset_id)

        request = DescribeDatasetRequest(
            dataset_id=dataset_id,
        )
        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Describe,
                request,
                timeout=timeout,
                expected_type=DescribeDatasetResponse
            )

        logger.info('Dataset %s successfully fetched', dataset_id)
        return self._dataset_impl._from_proto(proto=response.dataset, sdk=self._sdk)

    async def _list(
        self,
        *,
        status: UndefinedOr[DatasetStatusInput] = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        task_type: UndefinedOr[str] | Iterable[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[DatasetTypeT]:
        """Fetch a list of datasets based on specified filters.

        :param status: the status filter for datasets; can be a single status or an iterable of statuses.
        :param name_pattern: a pattern to filter dataset names.
        :param task_type: the type of task associated with the datasets; can be a single task type or an iterable of task types.
        :param timeout: the time to wait for the request.
            Defaults to 60 seconds.
        """
        status_: DatasetStatusInput = get_defined_value(status, [])  # type: ignore[assignment]
        status_list: list[SingleDatasetStatus] = [status_] if isinstance(status_, (str, DatasetStatus)) else list(status_)
        coerced_status_list: list[DatasetStatus] = [
            DatasetStatus._from_str(s) if isinstance(s, str) else s
            for s in status_list
        ]

        task_type_: str | Iterable[str] = get_defined_value(task_type, [])
        task_type_list: list[str] = [task_type_] if isinstance(task_type_, str) else list(task_type_)

        name_pattern_: str = get_defined_value(name_pattern, '')

        request = ListDatasetsRequest(
            folder_id=self._folder_id,
            status=coerced_status_list,  # type: ignore[arg-type]
            dataset_name_pattern=name_pattern_,
            task_type_filter=task_type_list,
        )

        logger.debug(
            'Fetching datasets list with status=%r, name_pattern=%r and task_type_filter=%r',
            coerced_status_list, name_pattern, task_type_list,
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.List,
                request,
                timeout=timeout,
                expected_type=ListDatasetsResponse,
            )

        logger.info('%d datasets successfully fetched', len(response.datasets))
        for dataset_info in response.datasets:
            yield self._dataset_impl._from_proto(proto=dataset_info, sdk=self._sdk)

    async def _list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        """Fetch available upload formats for a specified task type.

        :param task_type: the type of task for which to fetch upload formats.
        :param timeout: the time to wait for the request in seconds.
            Defaults to 60 seconds.
        """
        warnings.warn("dataset.list_upload_formats is deprecated", category=DeprecationWarning)

        logger.debug('Fetching available dataset upload formats for task_type=%s', task_type)
        request = ListUploadFormatsRequest(
            task_type=task_type
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.ListUploadFormats,
                request,
                timeout=timeout,
                expected_type=ListUploadFormatsResponse,
            )

        logger.info(
            '%d dataset upload formats successfully fetched for a task_type=%s',
            len(response.formats), task_type,
        )
        return tuple(response.formats)

    async def _list_upload_schemas(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[DatasetUploadSchema, ...]:
        """Fetch available upload schemas for a specified task type.

        :param task_type: the type of task for which to fetch upload schemas.
        :param timeout: the time to wait for the request in seconds.
            Defaults to 60 seconds.
        """
        logger.debug('Fetching available dataset upload schemas for task_type=%s', task_type)
        request = ListUploadSchemasRequest(
            task_type=task_type,
            folder_id=self._folder_id,
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.ListUploadSchemas,
                request,
                timeout=timeout,
                expected_type=ListUploadSchemasResponse,
            )

        logger.info(
            '%d dataset upload schemas successfully fetched for a task_type=%s',
            len(response.schemas), task_type,
        )
        return tuple(
            DatasetUploadSchema._from_proto(proto=schema, sdk=self._sdk)
            for schema in response.schemas
        )

@doc_from(BaseDatasets)
class AsyncDatasets(BaseDatasets[AsyncDataset, AsyncDatasetDraft]):
    _dataset_impl = AsyncDataset
    _dataset_draft_impl = AsyncDatasetDraft

    @doc_from(BaseDatasets._get)
    async def get(
        self,
        dataset_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncDataset:
        return await self._get(
            dataset_id=dataset_id,
            timeout=timeout
        )

    @doc_from(BaseDatasets._list)
    async def list(
        self,
        *,
        status: UndefinedOr[str] | DatasetStatus | Iterable[str | DatasetStatus] = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        task_type: UndefinedOr[str] | Iterable[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncDataset]:
        async for dataset in self._list(
            status=status,
            name_pattern=name_pattern,
            task_type=task_type,
            timeout=timeout,
        ):
            yield dataset

    @doc_from(BaseDatasets._list_upload_formats)
    async def list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return await self._list_upload_formats(task_type=task_type, timeout=timeout)

    @doc_from(BaseDatasets._list_upload_schemas)
    async def list_upload_schemas(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[DatasetUploadSchema, ...]:
        return await self._list_upload_schemas(task_type=task_type, timeout=timeout)

@doc_from(BaseDatasets)
class Datasets(BaseDatasets[Dataset, DatasetDraft]):
    _dataset_impl = Dataset
    _dataset_draft_impl = DatasetDraft

    __get = run_sync(BaseDatasets._get)
    __list = run_sync_generator(BaseDatasets._list)
    __list_upload_formats = run_sync(BaseDatasets._list_upload_formats)
    __list_upload_schemas = run_sync(BaseDatasets._list_upload_schemas)

    @doc_from(BaseDatasets._get)
    def get(
        self,
        dataset_id: str,
        *,
        timeout: float = 60,
    ) -> Dataset:
        return self.__get(
            dataset_id=dataset_id,
            timeout=timeout
        )

    @doc_from(BaseDatasets._list)
    def list(
        self,
        *,
        status: UndefinedOr[str] | DatasetStatus | Iterable[str | DatasetStatus] = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        task_type: UndefinedOr[str] | Iterable[str] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[Dataset]:
        yield from self.__list(
            status=status,
            name_pattern=name_pattern,
            task_type=task_type,
            timeout=timeout
        )

    @doc_from(BaseDatasets._list_upload_formats)
    def list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return self.__list_upload_formats(task_type=task_type, timeout=timeout)

    @doc_from(BaseDatasets._list_upload_schemas)
    def list_upload_schemas(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[DatasetUploadSchema, ...]:
        return self.__list_upload_schemas(task_type=task_type, timeout=timeout)
