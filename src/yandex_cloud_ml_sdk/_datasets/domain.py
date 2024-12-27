# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator

from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import (
    CreateDatasetRequest, CreateDatasetResponse, DescribeDatasetRequest, DescribeDatasetResponse, ListDatasetsRequest,
    ListDatasetsResponse, ListUploadFormatsRequest, ListUploadFormatsResponse
)
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .dataset import AsyncDataset, Dataset, DatasetTypeT
from .draft import AsyncDatasetDraft, DatasetDraft, DatasetDraftT
from .status import DatasetStatus
from .task_types import KnownTaskType, TaskTypeProxy


class BaseDatasets(BaseDomain, Generic[DatasetTypeT, DatasetDraftT]):
    _dataset_impl: type[DatasetTypeT]
    _dataset_draft_impl: type[DatasetDraftT]

    completions = TaskTypeProxy(KnownTaskType.TextToTextGeneration)
    text_classifiers_multilabel = TaskTypeProxy(KnownTaskType.TextClassificationMultilabel)
    text_classifiers_multiclass = TaskTypeProxy(KnownTaskType.TextClassificationMulticlass)
    text_classifiers_binary = TaskTypeProxy(KnownTaskType.TextClassificationMultilabel)

    def from_path_deferred(
        self,
        path: PathLike,
        *,
        task_type: UndefinedOr[str] = UNDEFINED,
        upload_format: UndefinedOr[str] = UNDEFINED,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        metadata: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
    ) -> DatasetDraftT:
        return self._dataset_draft_impl(
            _domain=self,
            path=path,
            task_type=get_defined_value(task_type, None),
            upload_format=get_defined_value(upload_format, None),
            name=get_defined_value(name, None),
            description=get_defined_value(description, None),
            metadata=get_defined_value(metadata, None),
            labels=get_defined_value(labels, None)
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
        timeout: float,
    ) -> DatasetTypeT:
        request = CreateDatasetRequest(
            folder_id=self._folder_id,
            task_type=task_type,
            upload_format=upload_format,
            name=name or '',
            description=description or '',
            metadata=metadata or '',
            labels=labels or {},
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=CreateDatasetResponse,
            )

        return self._dataset_impl._from_proto(proto=response.dataset, sdk=self._sdk)

    async def _get(
        self,
        dataset_id: str,
        *,
        timeout: float = 60,
    ) -> DatasetTypeT:
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

        return self._dataset_impl._from_proto(proto=response.dataset, sdk=self._sdk)

    async def _list(
        self,
        *,
        status: UndefinedOr[str] | DatasetStatus = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[DatasetTypeT]:
        status_: str | DatasetStatus = get_defined_value(status, DatasetStatus.STATUS_UNSPECIFIED)
        if isinstance(status_, str):
            status_ = DatasetStatus._from_str(status_)

        request = ListDatasetsRequest(
            folder_id=self._folder_id,
            status=status_,  # type: ignore[arg-type]
            dataset_name_pattern=get_defined_value(name_pattern, ''),
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.List,
                request,
                timeout=timeout,
                expected_type=ListDatasetsResponse,
            )

        for dataset_info in response.datasets:
            yield self._dataset_impl._from_proto(proto=dataset_info, sdk=self._sdk)

    async def _list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
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

        return tuple(response.formats)


class AsyncDatasets(BaseDatasets[AsyncDataset, AsyncDatasetDraft]):
    _dataset_impl = AsyncDataset
    _dataset_draft_impl = AsyncDatasetDraft

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

    async def list(
        self,
        *,
        status: UndefinedOr[str] | DatasetStatus = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncDataset]:
        async for dataset in self._list(
            status=status,
            name_pattern=name_pattern,
            timeout=timeout
        ):
            yield dataset

    async def list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return await self._list_upload_formats(task_type=task_type, timeout=timeout)


class Datasets(BaseDatasets[Dataset, DatasetDraft]):
    _dataset_impl = Dataset
    _dataset_draft_impl = DatasetDraft

    __get = run_sync(BaseDatasets._get)
    __list = run_sync_generator(BaseDatasets._list)
    __list_upload_formats = run_sync(BaseDatasets._list_upload_formats)

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

    def list(
        self,
        *,
        status: UndefinedOr[str] | DatasetStatus = UNDEFINED,
        name_pattern: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[Dataset]:
        yield from self.__list(
            status=status,
            name_pattern=name_pattern,
            timeout=timeout
        )

    def list_upload_formats(
        self,
        task_type: str,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return self.__list_upload_formats(task_type=task_type, timeout=timeout)
