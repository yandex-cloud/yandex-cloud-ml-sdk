# pylint: disable=no-name-in-module
from __future__ import annotations

import asyncio
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, TypeVar, AsyncIterator

import aiofiles
import httpx
from typing_extensions import Self
from yandex.cloud.ai.dataset.v1.dataset_pb2 import DatasetInfo as ProtoDatasetInfo
from yandex.cloud.ai.dataset.v1.dataset_pb2 import ValidationError as ProtoValidationError
from yandex.cloud.ai.dataset.v1.dataset_service_pb2 import (
    DeleteDatasetRequest, DeleteDatasetResponse, FinishMultipartUploadDraftRequest, FinishMultipartUploadDraftResponse,
    GetUploadDraftUrlRequest, GetUploadDraftUrlResponse, StartMultipartUploadDraftRequest,
    StartMultipartUploadDraftResponse, UpdateDatasetRequest, UpdateDatasetResponse, UploadedPartInfo,
    GetDownloadUrlsRequest, GetDownloadUrlsResponse
)
from yandex.cloud.ai.dataset.v1.dataset_service_pb2_grpc import DatasetServiceStub

from yandex_cloud_ml_sdk._logging import get_logger
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value, PathLike, coerce_path
from yandex_cloud_ml_sdk._types.resource import BaseDeleteableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync

from .status import DatasetStatus

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 100 * 1024 ** 2


@dataclasses.dataclass(frozen=True)
class ValidationErrorInfo:
    error: str
    description: str
    rows: tuple[int, ...]

    @classmethod
    def _from_proto(cls, proto: ProtoValidationError) -> ValidationErrorInfo:
        return cls(
            error=proto.error,
            description=proto.error_description,
            rows=tuple(proto.row_numbers)
        )


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
    allow_data_logging: bool

    status: DatasetStatus
    task_type: str
    rows: int
    size_bytes: int
    validation_errors: tuple[ValidationErrorInfo, ...]


@dataclasses.dataclass(frozen=True)
class BaseDataset(DatasetInfo, BaseDeleteableResource):
    @classmethod
    def _kwargs_from_message(cls, proto: ProtoDatasetInfo, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        kwargs['id'] = proto.dataset_id
        kwargs['created_by'] = proto.created_by_id
        kwargs['status'] = DatasetStatus._from_proto(proto.status)
        kwargs['validation_errors'] = tuple(
            ValidationErrorInfo._from_proto(p) for p in proto.validation_error
        )
        kwargs['allow_data_logging'] = proto.allow_data_log
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
        logger.debug("Updating dataset %s", self.id)
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

        logger.info("Dataset %s successfully updated", self.id)
        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        logger.debug("Deleting dataset %s", self.id)
        request = DeleteDatasetRequest(dataset_id=self.id)

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteDatasetResponse,
            )
            object.__setattr__(self, '_deleted', True)

        logger.info("Dataset %s successfully deleted", self.id)

    @safe_on_delete
    async def _download(
        self,
        *,
        download_path: PathLike,
        timeout: float = 60,
        exist_ok: bool = False,
    ) -> tuple[Path, ...]:
        logger.debug("Downloading dataset %s", self.id)

        base_path = coerce_path(download_path)
        if not base_path.exists():
            raise ValueError(f"{base_path} does not exist")

        if not base_path.is_dir():
            raise ValueError(f"{base_path} is not a directory")

        return await asyncio.wait_for(self.__download_impl(
            base_path=base_path,
            exist_ok=exist_ok,
        ), timeout)

    async def __download_impl(
        self,
        base_path: Path,
        exist_ok: bool,
    ) -> tuple[Path, ...]:
        urls = await self._get_download_urls()
        async with self._client.httpx() as client:
            coroutines = []
            for key, url in urls:
                file_path = base_path / key
                if file_path.exists() and not exist_ok:
                    raise ValueError(f"{file_path} already exists")

                coroutines.append(
                    self.__download_file(file_path, url, client),
                )

            await asyncio.gather(*coroutines)

        return tuple(base_path / key for key, _ in urls)

    async def __download_file(
        self,
        path: Path,
        url: str,
        client: httpx.AsyncClient,
    ) -> None:
        async with aiofiles.open(path, "wb") as file:
            async for chunk in self.__read_from_url(url, client):
                await file.write(chunk)

    async def __read_from_url(
        self,
        url: str,
        client: httpx.AsyncClient,
        chunk_size: int = 1024 * 1024 * 8,  # 8Mb
    ) -> AsyncIterator[bytes]:
        resp = await client.get(url)
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes(chunk_size=chunk_size):
            yield chunk

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
        logger.debug("Fetching upload url for dataset %s", self.id)
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

        logger.info("Dataset %s upload url successfully fetched", self.id)
        return result.upload_url

    async def _get_download_urls(
        self,
        *,
        timeout: float = 60,
    ) -> Iterable[tuple[str, str]]:
        logger.debug("Fetching download urls for dataset %s", self.id)

        request = GetDownloadUrlsRequest(
            dataset_id=self.id,
        )

        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            result = await self._client.call_service(
                stub.GetDownloadUrls,
                request,
                timeout=timeout,
                expected_type=GetDownloadUrlsResponse,
            )

        return [
            (r.key, r.url) for r in result.download_urls
        ]

    async def _start_multipart_upload(
        self,
        *,
        size_bytes: int,
        parts: int,
        timeout: float,
    ) -> tuple[str, ...]:
        logger.debug(
            "Starting multipart upload for dataset %s with size of %d bytes and %d parts",
            self.id, size_bytes, parts,
        )
        request = StartMultipartUploadDraftRequest(
            dataset_id=self.id,
            size_bytes=size_bytes,
            parts=parts,
        )
        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            result = await self._client.call_service(
                stub.StartMultipartUploadDraft,
                request,
                timeout=timeout,
                expected_type=StartMultipartUploadDraftResponse,
            )

        logger.info(
            "Multipart upload for dataset %s started and returned %d upload urls",
            self.id, len(result.multipart_upload_urls)
        )
        return tuple(result.multipart_upload_urls)

    async def _finish_multipart_upload(
        self,
        parts: Iterable[tuple[int, str]],
        timeout: float,
    ) -> None:
        parts_proto = [
            UploadedPartInfo(
                part_num=part_num,
                etag=etag
            ) for part_num, etag in parts
        ]
        logger.debug("Finishing multipart upload of dataset %s with %d parts", self.id, len(parts_proto))

        request = FinishMultipartUploadDraftRequest(
            dataset_id=self.id,
            uploaded_parts=parts_proto
        )
        async with self._client.get_service_stub(DatasetServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.FinishMultipartUploadDraft,
                request,
                timeout=timeout,
                expected_type=FinishMultipartUploadDraftResponse,
            )
        logger.debug("Multipart upload of dataset %s with %d parts finished", self.id, len(parts_proto))


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

    async def download(
        self,
        *,
        download_path: PathLike,
        timeout: float = 60,
        exist_ok: bool = False,
    ) -> tuple[Path, ...]:
        return await self._download(
            download_path=download_path,
            timeout=timeout,
            exist_ok=exist_ok,
        )


class Dataset(BaseDataset):
    __update = run_sync(BaseDataset._update)
    __delete = run_sync(BaseDataset._delete)
    __list_upload_formats = run_sync(BaseDataset._list_upload_formats)
    __download = run_sync(BaseDataset._download)

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

    def download(
        self,
        *,
        download_path: PathLike,
        timeout: float = 60,
        exist_ok: bool = False,
    ) -> tuple[Path, ...]:
        return self.__download(
            download_path=download_path,
            timeout=timeout,
            exist_ok=exist_ok,
        )


DatasetTypeT = TypeVar('DatasetTypeT', bound=BaseDataset)
