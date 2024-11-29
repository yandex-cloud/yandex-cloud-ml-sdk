from __future__ import annotations

import asyncio
import dataclasses
import functools
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

from google.protobuf.field_mask_pb2 import FieldMask  # pylint: disable=no-name-in-module
from typing_extensions import Concatenate, ParamSpec, Self

from yandex_cloud_ml_sdk._utils.proto import proto_to_dict

from .expiration import ExpirationConfig, ExpirationProtoType
from .misc import is_defined
from .result import BaseResult, ProtoMessage

if TYPE_CHECKING:
    from yandex_cloud_ml_sdk._client import AsyncCloudClient
    from yandex_cloud_ml_sdk._sdk import BaseSDK


@dataclasses.dataclass(frozen=True)
class BaseResource(BaseResult):
    id: str

    _sdk: BaseSDK = dataclasses.field(repr=False)

    @property
    def _client(self) -> AsyncCloudClient:
        return self._sdk._client

    @classmethod
    def _kwargs_from_message(cls, proto: ProtoMessage, sdk: BaseSDK) -> dict[str, Any]:  # pylint: disable=unused-argument
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
    def _from_proto(cls, *, proto: ProtoMessage, sdk: BaseSDK) -> Self:
        return cls(
            _sdk=sdk,
            **cls._kwargs_from_message(proto, sdk=sdk),
        )

    def _update_from_proto(self, proto: ProtoMessage) -> Self:
        # We want to Resource to be a immutable, but also we need
        # to maintain a inner status after updating and such
        kwargs = self._kwargs_from_message(proto, sdk=self._sdk)
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)
        return self

    def _fill_update_mask(self, mask: FieldMask, fields: dict[str, Any]) -> None:
        for key, value in fields.items():
            if is_defined(value):
                mask.paths.append(key)


@dataclasses.dataclass(frozen=True)
class BaseDeleteableResource(BaseResource):
    _lock: asyncio.Lock = dataclasses.field(repr=False)
    _deleted: bool = dataclasses.field(repr=False)

    @classmethod
    def _from_proto(cls, *, sdk: BaseSDK, proto: ProtoMessage) -> Self:
        return cls(
            _sdk=sdk,
            _lock=asyncio.Lock(),
            _deleted=False,
            **cls._kwargs_from_message(proto, sdk=sdk),
        )


@dataclasses.dataclass(frozen=True)
class ExpirableResource(BaseDeleteableResource):
    expiration_config: ExpirationConfig

    @classmethod
    def _kwargs_from_message(cls, proto: ExpirationProtoType, sdk: BaseSDK) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super()._kwargs_from_message(proto, sdk=sdk)  # type: ignore[arg-type]
        kwargs['expiration_config'] = ExpirationConfig.coerce(
            ttl_days=proto.expiration_config.ttl_days,
            expiration_policy=proto.expiration_config.expiration_policy,  # type: ignore[arg-type]
        )
        return kwargs


P = ParamSpec('P')
T = TypeVar('T')
R = TypeVar('R', bound=BaseDeleteableResource)


def safe_on_delete(
    method: Callable[Concatenate[R, P], Awaitable[T]]
) -> Callable[Concatenate[R, P], Awaitable[T]]:
    @functools.wraps(method)
    async def inner(self: R, *args: P.args, **kwargs: P.kwargs) -> T:
        async with self._lock:  # pylint: disable=protected-access
            action = method.__name__.lstrip('_')
            if self._deleted:  # pylint: disable=protected-access
                klass = self.__class__.__name__
                raise ValueError(f"you can't perform an action '{action}' on {klass}='{self.id}' because it is deleted")

            return await method(self, *args, **kwargs)

    return inner
