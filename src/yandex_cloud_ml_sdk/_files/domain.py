# pylint: disable=protected-access,no-name-in-module
from __future__ import annotations

from typing import AsyncIterator, Generic, Iterator

from yandex.cloud.ai.files.v1.file_pb2 import File as ProtoFile
from yandex.cloud.ai.files.v1.file_service_pb2 import (
    CreateFileRequest, GetFileRequest, ListFilesRequest, ListFilesResponse
)
from yandex.cloud.ai.files.v1.file_service_pb2_grpc import FileServiceStub

from yandex_cloud_ml_sdk._types.domain import BaseDomain
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, PathLike, UndefinedOr, coerce_path, get_defined_value, is_defined
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync, run_sync_generator

from .file import AsyncFile, File, FileTypeT


class BaseFiles(BaseDomain, Generic[FileTypeT]):
    """Files domain, which contains API for working with files.

    Files is a part of :ref:`Assistants API`, which is the only place you could use it.
    Provides upload, get and list methods that allow you to work with remote file objects you created earlier.
    """
    _file_impl: type[FileTypeT]

    async def _upload_bytes(
        self,
        data: bytes,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> FileTypeT:
        """Uploads a byte array as a file.

        :param data: The byte data to upload.
        :param name: The name of the file on the server.
        :param description: A description of the file.
        :param mime_type: The MIME type of the file.
            By default (i.e. when UNDEFINED) the server will try to auto-detect mime-type and you could override this file.
        :param labels: Labels associated with the file.
        :param ttl_days: Time-to-live in days for the file.
        :param expiration_policy: Expiration policy for the file.
            Assepts for passing :ref:`static` or :ref:`since_last_active` strings. Should be defined if :ref:`ttl_days` has been defined, otherwise both parameters should be undefined.
        :param timeout: Timeout for the operation in seconds.
            Defaults to 60 seconds.
        """
        if is_defined(ttl_days) != is_defined(expiration_policy):
            raise ValueError("ttl_days and expiration policy must be both defined either undefined")

        expiration_config = ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)

        request = CreateFileRequest(
            folder_id=self._folder_id,
            name=get_defined_value(name, ''),
            description=get_defined_value(description, ''),
            mime_type=get_defined_value(mime_type, ''),
            labels=get_defined_value(labels, {}),
            expiration_config=expiration_config.to_proto(),
            content=data,
        )

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Create,
                request,
                timeout=timeout,
                expected_type=ProtoFile,
            )

        return self._file_impl._from_proto(proto=response, sdk=self._sdk)

    async def _upload(
        self,
        path: PathLike,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> FileTypeT:
        """Uploads a file from a specified path.

        :param path: The path of the file to upload.
        :param name: The name of the file on the server.
        :param description: A description of the file.
        :param mime_type: The MIME type of the file.
            By default (i.e. when UNDEFINED) the server will try to auto-detect mime-type and you could override this file.
        :param labels: Labels associated with the file.
        :param ttl_days: Time-to-live in days for the file.
        :param expiration_policy: Expiration policy for the file.
            Assepts for passing :ref:`static` or :ref:`since_last_active` strings.
        :param timeout: Timeout for the operation in seconds.
            Defaults to 60.
        """
        path = coerce_path(path)
        return await self._upload_bytes(
            data=path.read_bytes(),
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    async def _get(
        self,
        file_id: str,
        *,
        timeout: float = 60,
    ) -> FileTypeT:
        """Retrieves a file by its ID.

        :param file_id: The unique identifier of the file to retrieve.
        :param timeout: Timeout for the operation in seconds.
            Defaults to 60.
        """
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

        return self._file_impl._from_proto(proto=response, sdk=self._sdk)

    async def _list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[FileTypeT]:
        """Lists Files in the SDK folder.

        :param page_size: The maximum number of files to return per page.
        :param timeout: Timeout for the operation in seconds.
            Defaults to 60.
        """
        page_token_ = ''
        page_size_ = get_defined_value(page_size, 0)

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            while True:
                request = ListFilesRequest(
                    folder_id=self._folder_id,
                    page_size=page_size_,
                    page_token=page_token_,
                )

                response = await self._client.call_service(
                    stub.List,
                    request,
                    timeout=timeout,
                    expected_type=ListFilesResponse,
                )
                for file_proto in response.files:
                    yield self._file_impl._from_proto(proto=file_proto, sdk=self._sdk)

                if not response.files:
                    return

                page_token_ = response.next_page_token

@doc_from(BaseFiles)
class AsyncFiles(BaseFiles[AsyncFile]):
    _file_impl = AsyncFile

    @doc_from(BaseFiles._upload_bytes)
    async def upload_bytes(
        self,
        data: bytes,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncFile:
        return await self._upload_bytes(
            data=data,
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    @doc_from(BaseFiles._upload)
    async def upload(
        self,
        path: PathLike,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncFile:
        return await self._upload(
            path=path,
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    @doc_from(BaseFiles._get)
    async def get(
        self,
        file_id: str,
        *,
        timeout: float = 60,
    ) -> AsyncFile:
        return await self._get(
            file_id=file_id,
            timeout=timeout
        )

    @doc_from(BaseFiles._list)
    async def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> AsyncIterator[AsyncFile]:
        async for file in self._list(
            page_size=page_size,
            timeout=timeout
        ):
            yield file

@doc_from(BaseFiles)
class Files(BaseFiles[File]):
    _file_impl = File

    __upload = run_sync(BaseFiles._upload)
    __upload_bytes = run_sync(BaseFiles._upload_bytes)
    __get = run_sync(BaseFiles._get)
    __list = run_sync_generator(BaseFiles._list)

    @doc_from(BaseFiles._upload_bytes)
    def upload_bytes(
        self,
        data: bytes,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> File:
        return self.__upload_bytes(
            data=data,
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    @doc_from(BaseFiles._upload)
    def upload(
        self,
        path: PathLike,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        mime_type: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> File:
        return self.__upload(
            path=path,
            name=name,
            description=description,
            mime_type=mime_type,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout
        )

    @doc_from(BaseFiles._get)
    def get(
        self,
        file_id: str,
        *,
        timeout: float = 60,
    ) -> File:
        return self.__get(
            file_id=file_id,
            timeout=timeout
        )

    @doc_from(BaseFiles._list)
    def list(
        self,
        *,
        page_size: UndefinedOr[int] = UNDEFINED,
        timeout: float = 60
    ) -> Iterator[File]:
        yield from self.__list(
            page_size=page_size,
            timeout=timeout
        )
