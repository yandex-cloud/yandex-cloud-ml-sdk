# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TypeVar

from typing_extensions import Self
from yandex.cloud.ai.files.v1.file_pb2 import File as ProtoFile
from yandex.cloud.ai.files.v1.file_service_pb2 import (
    DeleteFileRequest, DeleteFileResponse, GetFileUrlRequest, GetFileUrlResponse, UpdateFileRequest
)
from yandex.cloud.ai.files.v1.file_service_pb2_grpc import FileServiceStub

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.doc import doc_from
from yandex_cloud_ml_sdk._utils.sync import run_sync


@dataclasses.dataclass(frozen=True)
class BaseFile(ExpirableResource):
    @safe_on_delete
    async def _get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
        """Retrieve the URL for the file.

        This method constructs a request to get the temporary URL for downloading the file and returns it.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        :return: The URL of the file given as a string.
        """
        request = GetFileUrlRequest(file_id=self.id)

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                 stub.GetUrl,
                 request,
                 timeout=timeout,
                 expected_type=GetFileUrlResponse,
             )

        return response.url

    @safe_on_delete
    async def _update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> Self:
        """Update the properties of the file.

        This method allows updating various properties of the file, such as
        its name, description, labels, TTL (time-to-live) days, and expiration policy.
        Note that only the fields explicitly passed will be updated.
        You can also pass None, which will reset it.
        Keep in mind that the method is mutating and modifies the file object in-place.

        :param name: The new name for the updated file.
        :param description: The new description for the file.
        :param labels: A dictionary of labels to associate with the file.
        :param ttl_days: The new TTL (time-to-live) for the file in days.
        :param expiration_policy: The new expiration policy for the file.
            Assepts for passing :ref:`static` or :ref:`since_last_active` strings.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        :return: The updated instance of the file.
        """
        # pylint: disable=too-many-locals
        name_ = get_defined_value(name, '')
        description_ = get_defined_value(description, '')
        labels_ = get_defined_value(labels, {})

        expiration_config = ExpirationConfig.coerce(
            ttl_days=ttl_days,
            expiration_policy=expiration_policy
        )

        request = UpdateFileRequest(
            file_id=self.id,
            name=name_,
            description=description_,
            labels=labels_,
            expiration_config=expiration_config.to_proto()
        )
        self._fill_update_mask(
            request.update_mask,
            {
                'name': name,
                'description': description,
                'labels': labels,
                'expiration_config.ttl_days': ttl_days,
                'expiration_config.expiration_policy': expiration_policy
            }
        )

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            response = await self._client.call_service(
                stub.Update,
                request,
                timeout=timeout,
                expected_type=ProtoFile,
            )
        self._update_from_proto(response)

        return self

    @safe_on_delete
    async def _delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        """Delete the file.

        This method constructs and executes a request to delete the file associated
        with the current instance.

        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        """
        request = DeleteFileRequest(file_id=self.id)

        async with self._client.get_service_stub(FileServiceStub, timeout=timeout) as stub:
            await self._client.call_service(
                stub.Delete,
                request,
                timeout=timeout,
                expected_type=DeleteFileResponse,
            )
            object.__setattr__(self, '_deleted', True)

    @safe_on_delete
    async def _download_as_bytes(
        self,
        *,
        chunk_size: int = 32768,
        timeout: float = 60
    ) -> bytes:
        """Download the file as bytes.

        This method retrieves the file's URL and streams the file's content as whole
        (this may overflow the user's memory), returning it as a byte string.

        :param chunk_size: The size of each chunk to read from the stream in bytes.
        :param timeout: Timeout, or the maximum time to wait for the request to complete in seconds.
            Defaults to 60 seconds.
        :return: The file contents as bytes.
        """
        # I didn't invent better way to use this function without a @safe_on_delete-lock
        url = await self._get_url.__wrapped__(self, timeout=timeout)  # type: ignore[attr-defined]

        async with self._client.httpx() as client:
            async with client.stream("GET", url, timeout=timeout) as response:
                response.raise_for_status()

                file_bytes = b''
                async for chunk in response.aiter_bytes(chunk_size):
                    file_bytes += chunk

                return file_bytes


@dataclasses.dataclass(frozen=True)
class RichFile(BaseFile):
    """A detailed representation of the file enriched with additional metadata.

    This class extends BaseFile by including additional attributes such as
    name, description, MIME type, creating and updating details,
    expiration date, and labels.
    """
    # The name of the file
    name: str | None
    # A description of the file
    description: str | None
    # The MIME type of the file
    mime_type: str
    # Identifier of the user who created the file
    created_by: str
    # Timestamp when the file was created
    created_at: datetime
    # Identifier of the user who last updated the file
    updated_by: str
    # Timestamp when the file was last updated
    updated_at: datetime
    # Timestamp when the file is set to expire
    expires_at: datetime
    # A dictionary of labels associated with the file
    labels: dict[str, str] | None


class AsyncFile(RichFile):
    @doc_from(BaseFile._get_url)
    async def get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
        return await self._get_url(
            timeout=timeout
        )

    @doc_from(BaseFile._update)
    async def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> AsyncFile:
        return await self._update(
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout,
        )

    @doc_from(BaseFile._delete)
    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(
            timeout=timeout
        )

    @doc_from(BaseFile._download_as_bytes)
    async def download_as_bytes(
        self,
        *,
        chunk_size: int = 32768,
        timeout: float = 60
    ) -> bytes:
        return await self._download_as_bytes(
            chunk_size=chunk_size,
            timeout=timeout
        )


class File(RichFile):
    __get_url = run_sync(RichFile._get_url)
    __update = run_sync(RichFile._update)
    __delete = run_sync(RichFile._delete)
    __download_as_bytes = run_sync(RichFile._download_as_bytes)

    @doc_from(BaseFile._get_url)
    def get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
        return self.__get_url(
            timeout=timeout
        )

    @doc_from(BaseFile._update)
    def update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        ttl_days: UndefinedOr[int] = UNDEFINED,
        expiration_policy: UndefinedOr[ExpirationPolicyAlias] = UNDEFINED,
        timeout: float = 60,
    ) -> File:
        return self.__update(
            name=name,
            description=description,
            labels=labels,
            ttl_days=ttl_days,
            expiration_policy=expiration_policy,
            timeout=timeout,
        )

    @doc_from(BaseFile._delete)
    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(
            timeout=timeout
        )

    @doc_from(BaseFile._download_as_bytes)
    def download_as_bytes(
        self,
        *,
        chunk_size: int = 32768,
        timeout: float = 60
    ) -> bytes:
        return self.__download_as_bytes(
            chunk_size=chunk_size,
            timeout=timeout
        )

FileTypeT = TypeVar('FileTypeT', bound=BaseFile)
