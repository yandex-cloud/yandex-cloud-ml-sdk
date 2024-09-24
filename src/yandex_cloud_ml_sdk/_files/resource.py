# pylint: disable=protected-access
from __future__ import annotations

from typing import Generic, TypeVar

from yandex.cloud.ai.files.v1.file_pb2 import File as ProtoFile
from yandex.cloud.ai.files.v1.file_service_pb2 import (
    CreateFileRequest, GetFileRequest, ListFilesRequest, ListFilesResponse
)
from yandex.cloud.ai.files.v1.file_service_pb2_grpc import FileServiceStub

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, coerce_path, get_defined_value
from yandex_cloud_ml_sdk._types.resource import BaseResource
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .function import AsyncFile, BaseFile, File

FileTypeT = TypeVar('FileTypeT', bound=BaseFile)


class BaseFiles(BaseResource, Generic[FileTypeT]):
    _file_impl: type[FileTypeT]

    async def _upload_bytes(
        self,
        data: bytes,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> FileTypeT:
        name = get_defined_value(name, None)
        description = get_defined_value(description, None)
        mime_type = get_defined_value(mime_type, None)
        labels = get_defined_value(labels, None)

        request = CreateFileRequest(
            folder_id=self._folder_id,
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            content=data,
        )

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoFile,
            )

        return self._file_impl.from_proto(proto=response, files=self, sdk=self._sdk)

    async def _upload(
        self,
        path: PathLike,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> FileTypeT:
        path = coerce_path(path)
        return await self._upload_bytes(
            data=path.read_bytes(),
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            timeout=timeout
        )

    async def _get(
        self,
        file_id: str,
        *,
        timeout: float = 60,
    ):
        # TODO: we need a global per-sdk cache on file_ids to rule out
        # possibility we have two Files with same ids but different fields
        request = GetFileRequest(file_id=file_id)

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Get,
                request,
                timeout=timeout,
                expected_type=ProtoFile,
            )

        return self._file_impl.from_proto(proto=response, files=self, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        page_token: UndefinedOr[str] = UNDEFINED,
        timeout: float = 60
    ):
        page_token = get_defined_value(page_token, None)
        page_size = get_defined_value(page_size, None)

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            while True:
                request = ListFilesRequest(
                    folder_id=self._folder_id,
                    page_size=page_size,
                    page_token=page_token,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListFilesResponse,
                )
                for file_proto in response.files:
                    yield self._file_impl.from_proto(proto=file_proto, files=self, sdk=self._sdk)

                if not response.files:
                    return

                page_token = response.next_page_token


class AsyncFiles(BaseFiles[AsyncFile]):
    _file_impl = AsyncFile

    upload = BaseFiles._upload
    upload_bytes = BaseFiles._upload_bytes
    get = BaseFiles._get
    list = BaseFiles._list


class Files(BaseFiles[File]):
    _file_impl = File

    upload = run_sync(BaseFiles._upload)
    upload_bytes = run_sync(BaseFiles._upload_bytes)
    get = run_sync(BaseFiles._get)
    list = run_sync_generator(BaseFiles._list)
