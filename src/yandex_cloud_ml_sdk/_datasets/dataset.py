# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo as ProtoDatasetInfo
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import (
    DeleteDatasetRequest, DeleteDatasetResponse, GetUploadDraftUrlRequest, GetUploadDraftUrlResponse,
    UpdateDatasetRequest, UpdateDatasetResponse
)
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import BaseDeleteableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .status import DatasetStatus

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


DEFAULT_CHUNK_SIZE = 100 * 1024 ** 2


@dataclasses.dataclass(frozen=True)
class DatasetInfo:
    folder_id: str
    name: str | None
    description: str | None
    metadata: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    labels: dict[str, str] | None

    status: DatasetStatus
    task_type: str
    rows: int
    size_bytes: int


@dataclasses.dataclass(frozen=True)
class BaseDataset(DatasetInfo, BaseDeleteableResource):
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoDatasetInfo, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        kwargs['id'] = proto.dataset_id
        kwargs['created_by'] = proto.created_by_id
        kwargs['status'] = DatasetStatus._from_proto(proto.status)
        return kwargs

    @safe_on_delete
    async def _update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        request = UpdateDatasetRequest(
            dataset_id=self.id,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            labels=get_defined_value(labels, {}),
        )

        self._fill_update_mask(
            request.update_mask,
            {
                'name': name,
                'description': description,
                'labels': labels,
            }
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Update,
                request,
                timeout=timeout,
                expected_type=UpdateDatasetResponse,
            )
        self._update_from_proto(response.dataset)

        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        request = DeleteDatasetRequest(dataset_id=self.id)

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteDatasetResponse,
            )
            object.__setattr__(self, '_deleted', True)

    async def _list_upload_formats(
        self,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        # pylint: disable=protected-access
        return await self._sdk.datasets._list_upload_formats(
            task_type=self.task_type,
            timeout=timeout
        )

    async def _get_upload_url(
        self,
        *,
        size: int,
        timeout: float = 60,
    ) -> str:
        request = GetUploadDraftUrlRequest(
            dataset_id=self.id,
            size_bytes=size
        )
        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            result = await self._client.call_service(
                stub.GetUploadDraftUrl,
                request,
                timeout=timeout,
                expected_type=GetUploadDraftUrlResponse,
            )

        return result.upload_url


class AsyncDataset(BaseDataset):
    async def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return await self._update(
            name=name,
            description=description,
            labels=labels,
            timeout=timeout
        )

    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(timeout=timeout)

    async def list_upload_formats(
        self,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return await self._list_upload_formats(timeout=timeout)


class Dataset(BaseDataset):
    __update = run_sync(BaseDataset._update)
    __delete = run_sync(BaseDataset._delete)
    __list_upload_formats = run_sync(BaseDataset._list_upload_formats)

    def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        return self.__update(
            name=name,
            description=description,
            labels=labels,
            timeout=timeout
        )

    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(timeout=timeout)

    def list_upload_formats(
        self,
        *,
        timeout: float = 60,
    ) -> tuple[str, ...]:
        return self.__list_upload_formats(timeout=timeout)


DatasetTypeT = TypeVar('DatasetTypeT', bound=BaseDataset)
