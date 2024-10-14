from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypedDict, Union, cast

from typing_extensions import NotRequired
from yandex.cloud.ai.common.common_pb2 import (
    ExpirationConfig as ExpirationConfigProto  # pylint: disable=no-name-in-module
)


class ExpirationPolicy(Enum):
    UNSPECIFIED = ExpirationConfigProto.EXPIRATION_POLICY_UNSPECIFIED
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
            self.UNSPECIFIED: ExpirationConfigProto.EXPIRATION_POLICY_UNSPECIFIED,
            self.STATIC: ExpirationConfigProto.STATIC,
            self.SINCE_LAST_ACTIVE: ExpirationConfigProto.SINCE_LAST_ACTIVE
        }[self]  # type: ignore[index]


ExpirationPolicyTypeT = Union[
    ExpirationPolicy,
    Literal[0, 1, 2],
    Literal['UNSPECIFIED', 'STATIC', 'SINCE_LAST_ACTIVE'],
    Literal['unspecified', 'static', 'since_last_active'],
]


class ExpirationConfigDict(TypedDict):
    ttl_days: NotRequired[int]
    policy: NotRequired[ExpirationPolicyTypeT]


@dataclass(frozen=True)
class ExpirationConfig:
    ttl_days: int | None = None
    policy: ExpirationPolicy | None = None

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
            if raw_policy := value.get('policy'):
                policy = ExpirationPolicy.coerce(raw_policy)
        elif value is not None:
            raise TypeError(f"wrong type to use as alias for cls {cls}")

        return cls(
            ttl_days=ttl_days,
            policy=policy
        )

    def to_proto(self):
        return ExpirationConfigProto(
            expiration_policy=self.policy.to_proto() if self.policy else None,
            ttl_days=self.ttl_days
        )


ExpirationConfigT = Union[ExpirationConfig, ExpirationConfigDict, int, ExpirationPolicyTypeT]
