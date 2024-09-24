from __future__ import annotations

import dataclasses
import functools
from asyncio import Lock
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import httpx
from typing_extensions import ParamSpec, Self
from yandex.cloud.ai.files.v1.file_pb2 import File as ProtoFile
from yandex.cloud.ai.files.v1.file_service_pb2 import (
    DeleteFileRequest, DeleteFileResponse, GetFileUrlRequest, GetFileUrlResponse, UpdateFileRequest
)
from yandex.cloud.ai.files.v1.file_service_pb2_grpc import FileServiceStub

from yandex_cloud_ml_sdk._types.misc import UNDEFINED, UndefinedOr, get_defined_value
from yandex_cloud_ml_sdk._utils.proto import proto_to_dict
from yandex_cloud_ml_sdk._utils.sync import run_sync

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._client import AsyncCloudClient
    from yandex_cloud_ml_sdk._files.resource import BaseFiles
    from yandex_cloud_ml_sdk._sdk import BaseSDK


P = ParamSpec('P')
T = TypeVar('T')


def safe(method: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(method)
    async def inner(self: BaseFile, *args: P.args, **kwargs: P.kwargs) -> T:
        async with self._lock:
            action = method.__name__.lstrip('_')
            if self._deleted:
                raise ValueError("you can't perform an action '{action}' on file '{self.id}' because it is deleted")

            return await method(self, *args, **kwargs)

    return inner


@dataclasses.dataclass(frozen=True)
class BaseFile:
    _sdk: BaseSDK = dataclasses.field(repr=False)
    _files: BaseFiles = dataclasses.field(repr=False)
    _lock: Lock = dataclasses.field(repr=False)
    _deleted: bool = dataclasses.field(repr=False)

    id: str

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    def _assert_not_deleted(self, action: str) -> None:
        if self._deleted:
            raise ValueError(f"you can't perform action '{action}' on this file because it is deleted")

    @safe
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

    @safe
    async def _update(
        self,
        *,
        name: UndefinedOr[str] = UNDEFINED,
        description: UndefinedOr[str] = UNDEFINED,
        labels: UndefinedOr[dict[str, str]] = UNDEFINED,
        timeout: float = 60,
    ) -> None:
        name = get_defined_value(name, None)
        description = get_defined_value(description, None)
        labels = get_defined_value(labels, None)

        request = UpdateFileRequest(
            file_id=self.id,
            name=name,
            description=description,
            labels=labels,
        )

        for key, value in (
            ('name', name),
            ('description', description),
            ('labels', labels)
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

    @safe
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

    @safe
    async def _download_as_bytes(
        self,
        *,
        chunk_size: int = 32768,
        timeout: float = 60
    ) -> bytes:
        # to use this function without a @safe-lock
        url = await self._get_url.__wrapped__(self, timeout=timeout)

        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, timeout=timeout) as response:
                response.raise_for_status()

                file_bytes = b''
                async for chunk in response.aiter_bytes(chunk_size):
                    file_bytes += chunk

                return file_bytes

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoFile) -> dict[str, Any]:
        fields = dataclasses.fields(cls)
        data = proto_to_dict(proto)
        kwargs = {}
        for field in fields:
            name = field.name
            if name.startswith('_'):
                continue

            kwargs[name] = data.get(name)

        return kwargs

    @classmethod
    def from_proto(cls, *, files: BaseFiles, sdk: BaseSDK, proto: ProtoFile) -> Self:
        return cls(
            _sdk=sdk,
            _files=files,
            _lock=Lock(),
            _deleted=False,
            **cls._kwargs_from_message(proto),
        )

    def _update_from_proto(self, proto: ProtoFile) -> Self:
        # We want to File to be a immutable, but also we need
        # to maintain a inner status after updating and such
        kwargs = self._kwargs_from_message(proto)
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)
        return self


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
