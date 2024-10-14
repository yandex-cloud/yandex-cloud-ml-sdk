from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypedDict, Union, cast

from typing_extensions import NotRequired
from yandex.cloud.ai.common.common_pb2 import (
    ExpirationConfig as ExpirationConfigProto  # pylint: disable=no-name-in-module
)

from .misc import Undefined, is_defined


class ExpirationPolicy(Enum):
    STATIC = ExpirationConfigProto.STATIC
    SINCE_LAST_ACTIVE = ExpirationConfigProto.SINCE_LAST_ACTIVE

    @classmethod
    def coerce(cls, value: ExpirationPolicyTypeT) -> ExpirationPolicy:
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        if isinstance(value, str):
            if member := cls.__members__.get(value.upper()):
                return member
            raise ValueError(f'wrong value {value} for use as an alisas for {cls}')
        raise TypeError(f'wrong type for use as an alias for {cls}')

    def to_proto(self) -> int:
        return {
            self.STATIC: ExpirationConfigProto.STATIC,
            self.SINCE_LAST_ACTIVE: ExpirationConfigProto.SINCE_LAST_ACTIVE
        }[self]  # type: ignore[index]


ExpirationPolicyTypeT = Union[
    ExpirationPolicy,
    Literal[0, 1, 2],
    Literal['STATIC', 'SINCE_LAST_ACTIVE'],
    Literal['static', 'since_last_active'],
]


class ExpirationConfigDict(TypedDict):
    ttl_days: NotRequired[int] | None
    expiration_policy: NotRequired[ExpirationPolicyTypeT] | None


@dataclass(frozen=True)
class ExpirationConfig:
    ttl_days: int | None = None
    expiration_policy: ExpirationPolicy | None = None

    def is_defined(self) -> bool:
        return bool(
            self.ttl_days and
            self.expiration_policy
        )

    def is_partially_defined(self) -> bool:
        return bool(
            self.ttl_days or
            self.expiration_policy
        )

    @classmethod
    def coerce(cls, value: ExpirationConfigT | None) -> ExpirationConfig:
        if isinstance(value, ExpirationConfig):
            return value

        ttl_days: int | None = None
        policy: ExpirationPolicy | None = None
        if isinstance(value, int):
            ttl_days = value
        elif isinstance(value, (str, ExpirationPolicy)):
            policy = ExpirationPolicy.coerce(value)
        elif isinstance(value, dict):
            value = cast(ExpirationConfigDict, value)
            ttl_days = value.get('ttl_days')
            if raw_policy := value.get('expiration_policy'):
                policy = ExpirationPolicy.coerce(raw_policy)
        elif value is None or not is_defined(value):
            pass
        else:
            raise TypeError(f"wrong type to use as alias for cls {cls}")

        return cls(
            ttl_days=ttl_days,
            expiration_policy=policy
        )

    @classmethod
    def coerce_strict(cls, value: ExpirationConfigT | None) -> ExpirationConfig:
        config = cls.coerce(value)
        if (
            config is not None
            and not config.is_defined()
            and config.is_partially_defined()
        ):
            raise ValueError(
                'At this place both exporation_config.ttl_days and expiration_config.policy must be defined '
                'or neither'
            )
        return config

    def to_proto(self) -> ExpirationConfigProto | None:
        if not self.is_partially_defined():
            return None

        return ExpirationConfigProto(
            expiration_policy=self.expiration_policy.to_proto() if self.expiration_policy else None,
            ttl_days=self.ttl_days
        )


ExpirationConfigT = Union[ExpirationConfig, ExpirationConfigDict, int, ExpirationPolicyTypeT, Undefined]
ExpirationConfigStrictT = Union[ExpirationConfig, ExpirationConfigDict, Undefined]
