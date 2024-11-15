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

from yandex_cloud_ml_sdk._client import httpx_client
from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import ExpirableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync


@dataclasses.dataclass(frozen=True)
class BaseFile(ExpirableResource):
    @safe_on_delete
    async def _get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
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
        # I didn't invent better way to use this function without a @safe_on_delete-lock
        url = await self._get_url.__wrapped__(self, timeout=timeout)  # type: ignore[attr-defined]

        async with httpx_client() as client:
            async with client.stream("GET", url, timeout=timeout) as response:
                response.raise_for_status()

                file_bytes = b''
                async for chunk in response.aiter_bytes(chunk_size):
                    file_bytes += chunk

                return file_bytes


@dataclasses.dataclass(frozen=True)
class RichFile(BaseFile):
    name: str | None
    description: str | None
    mime_type: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    expires_at: datetime
    labels: dict[str, str] | None


class AsyncFile(RichFile):
    async def get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
        return await self._get_url(
            timeout=timeout
        )

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

    async def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        await self._delete(
            timeout=timeout
        )

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

    def get_url(
        self,
        *,
        timeout: float = 60
    ) -> str:
        return self.__get_url(
            timeout=timeout
        )

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

    def delete(
        self,
        *,
        timeout: float = 60,
    ) -> None:
        self.__delete(
            timeout=timeout
        )

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
