# pylint: disable=no-name-in-module
from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import TYPE_CHECKING, Any

import httpx
from typing_extensions import Self
from yandex.cloud.ai.files.v1.file_pb2 import File as ProtoFile
from yandex.cloud.ai.files.v1.file_service_pb2 import (
    DeleteFileRequest, DeleteFileResponse, GetFileUrlRequest, GetFileUrlResponse, UpdateFileRequest
)
from yandex.cloud.ai.files.v1.file_service_pb2_grpc import FileServiceStub

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationPolicyAlias
from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._types.resource import BaseDeleteableResource, safe_on_delete
from yandex_cloud_ml_sdk._utils.sync import run_sync

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseFile(BaseDeleteableResource):
    expiration_config: ExpirationConfig

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoFile, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)
        kwargs['expiration_config'] = ExpirationConfig.coerce(
            ttl_days=proto.expiration_config.ttl_days,
            expiration_policy=proto.expiration_config.expiration_policy,  # type: ignore[arg-type]
        )
        return kwargs

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
        for key, value in (
            ('name', name_),
            ('description', description_),
            ('labels', labels_),
            ('expiration_config.ttl_days', expiration_config.ttl_days),
            ('expiration_config.expiration_policy', expiration_config.expiration_policy),
        ):
            if value is not None:
                request.update_mask.paths.append(key)

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

        async with httpx.AsyncClient() as client:
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
    get_url = RichFile._get_url
    update = RichFile._update
    delete = RichFile._delete
    download_as_bytes = RichFile._download_as_bytes


class File(RichFile):
    get_url = run_sync(RichFile._get_url)
    update = run_sync(RichFile._update)
    delete = run_sync(RichFile._delete)
    download_as_bytes = run_sync(RichFile._download_as_bytes)
