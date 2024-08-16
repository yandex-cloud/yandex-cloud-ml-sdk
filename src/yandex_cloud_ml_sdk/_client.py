# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, Protocol, Sequence, TypeVar, cast

import grpc
import grpc.aio
from google.protobuf.message import Message
from yandex.cloud.endpoint.api_endpoint_service_pb2 import ListApiEndpointsRequest  # pylint: disable=no-name-in-module
from yandex.cloud.endpoint.api_endpoint_service_pb2_grpc import ApiEndpointServiceStub
from yandexcloud._sdk import _service_for_ctor

from ._auth import BaseAuth, get_auth_provider
from ._retry import RETRY_KIND_METADATA_KEY, RetryKind, RetryPolicy
from ._utils.lock import LazyLock


class StubType(Protocol):
    def __init__(self, channel: grpc.Channel | grpc.aio.Channel) -> None:
        ...


_T = TypeVar('_T', bound=StubType)
_D = TypeVar('_D', bound=Message)


class AsyncCloudClient:
    def __init__(
        self,
        *,
        endpoint: str,
        auth: BaseAuth | str | None,
        service_map: dict[str, str],
        interceptors: Sequence[grpc.aio.ClientInterceptor] | None,
        yc_profile: str | None,
        retry_policy: RetryPolicy,
    ):
        self._endpoint = endpoint
        self._auth = auth
        self._auth_provider: BaseAuth | None = None
        self._yc_profile = yc_profile

        self._service_map_override: dict[str, str] = service_map
        self._service_map: dict[str, str] = {}

        self._interceptors = (
            (tuple(interceptors) if interceptors else ()) +
            retry_policy.get_interceptors()
        )

        self._channels: dict[type[StubType], grpc.aio.Channel] = {}

        self._auth_lock = LazyLock()
        self._channels_lock = LazyLock()

    async def _init_service_map(self, timeout: float):
        credentials = grpc.ssl_channel_credentials()
        metadata = await self._get_metadata(auth_required=False, timeout=timeout, retry_kind=RetryKind.SINGLE)
        async with grpc.aio.secure_channel(
            self._endpoint,
            credentials,
            interceptors=self._interceptors,
        ) as channel:
            stub = ApiEndpointServiceStub(channel)
            response = await stub.List(
                ListApiEndpointsRequest(),
                timeout=timeout,
                metadata=metadata,
            )  # type: ignore[misc]
            for endpoint in response.endpoints:
                self._service_map[endpoint.id] = endpoint.address

        # TODO: add a validation for unknown services in override
        self._service_map.update(self._service_map_override)

    async def _get_metadata(
        self,
        *,
        auth_required: bool,
        timeout: float,
        retry_kind: RetryKind = RetryKind.NONE,
    ) -> tuple[tuple[str, str], ...]:
        metadata = (
            (RETRY_KIND_METADATA_KEY, retry_kind.name),
        )

        if not auth_required:
            return metadata

        if self._auth_provider is None:
            async with self._auth_lock():
                if self._auth_provider is None:
                    self._auth_provider = await get_auth_provider(
                        auth=self._auth,
                        endpoint=self._endpoint,
                        yc_profile=self._yc_profile
                    )

        # in case of self._auth=NoAuth(), it will return None
        # and it is might be okay: for local installations and on-premises
        auth = await self._auth_provider.get_auth_metadata(client=self, timeout=timeout, lock=self._auth_lock())

        if auth:
            return metadata + (auth, )

        return metadata

    def _new_channel(self, endpoint: str) -> grpc.aio.Channel:
        credentials = grpc.ssl_channel_credentials()
        return grpc.aio.secure_channel(
            endpoint,
            credentials,
            interceptors=self._interceptors,
        )

    async def _get_channel(self, stub_class: type[_T], timeout: float) -> grpc.aio.Channel:
        if stub_class in self._channels:
            return self._channels[stub_class]

        async with self._channels_lock():
            if stub_class in self._channels:
                return self._channels[stub_class]

            service_name: str = _service_for_ctor(stub_class)

            if not self._service_map:
                await self._init_service_map(timeout=timeout)

            if not (endpoint := self._service_map.get(service_name)):
                raise ValueError(f'failed to find endpoint for {service_name=} and {stub_class=}')

            channel = self._channels[stub_class] = self._new_channel(endpoint)
            return channel

    @asynccontextmanager
    async def get_service_stub(self, stub_class: type[_T], timeout: float) -> AsyncIterator[_T]:
        # NB: right now get_service_stub is asynccontextmanager and it is unnecessary,
        # but in future if we will make some ChannelPool, it could be handy to know,
        # when "user" releases resource
        channel = await self._get_channel(stub_class, timeout)
        yield stub_class(channel)

    async def call_service_stream(
        self,
        service: grpc.aio.UnaryStreamMultiCallable | grpc.UnaryStreamMultiCallable,
        request: Message,
        timeout: float,
        expected_type: type[_D],  # pylint: disable=unused-argument
        auth: bool = True,
        retry_kind: Literal[RetryKind.NONE, RetryKind.SINGLE, RetryKind.CONTINUATION] = RetryKind.SINGLE,
    ) -> AsyncIterator[_D]:
        # NB: when you instantiate a stub class on a async or sync channel, you got
        # "async" of "sync" stub, and it have relevant methods like __aiter__
        # and such. But from typing perspective it have no difference,
        # it just a stub object.
        # Auto-generated stubs for grpc saying, that attribute stub.Service returns
        # grpc.Unary...Multicallable, not async one, but in real life
        # we are using only async stubs in this project.
        # In ideal world we need to do something like
        # cast(grpc.aio.UnaryStreamMultiCallable, stub.Service) at usage place,
        # but it is too lot places to insert this cast, so I'm doing it here.
        service = cast(grpc.aio.UnaryStreamMultiCallable, service)

        metadata = await self._get_metadata(auth_required=auth, timeout=timeout, retry_kind=retry_kind)
        call = service(request, metadata=metadata, timeout=timeout)

        try:
            async for response in call:
                yield cast(_D, response)
        except GeneratorExit:
            call.cancel()
            raise

    async def call_service(
        self,
        service: grpc.aio.UnaryUnaryMultiCallable | grpc.UnaryUnaryMultiCallable,
        request: Message,
        timeout: float,
        expected_type: type[_D],  # pylint: disable=unused-argument
        auth: bool = True,
        retry_kind: Literal[RetryKind.NONE, RetryKind.SINGLE] = RetryKind.SINGLE,
    ) -> _D:
        service = cast(grpc.aio.UnaryUnaryMultiCallable, service)

        metadata = await self._get_metadata(auth_required=auth, timeout=timeout, retry_kind=retry_kind)
        result = await service(
            request,
            metadata=metadata,
            timeout=timeout,
            wait_for_ready=True,
        )
        return cast(_D, result)
