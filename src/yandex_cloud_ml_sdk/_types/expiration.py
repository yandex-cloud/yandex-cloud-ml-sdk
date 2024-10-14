from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Union

# pylint: disable-next=no-name-in-module
from yandex.cloud.ai.common.common_pb2 import ExpirationConfig as ExpirationConfigProto

from .misc import UndefinedOr, get_defined_value


class ExpirationPolicy(Enum):
    STATIC = ExpirationConfigProto.STATIC
    SINCE_LAST_ACTIVE = ExpirationConfigProto.SINCE_LAST_ACTIVE

    @classmethod
    def coerce(cls, value: ExpirationPolicyAlias) -> ExpirationPolicy:
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


ExpirationPolicyAlias = Union[
    ExpirationPolicy,
    Literal[1, 2],
    Literal['STATIC', 'SINCE_LAST_ACTIVE'],
    Literal['static', 'since_last_active'],
]


@dataclass(frozen=True)
class ExpirationConfig:
    ttl_days: int | None = None
    expiration_policy: ExpirationPolicy | None = None

    @classmethod
    def coerce(
        cls,
        ttl_days: UndefinedOr[int],
        expiration_policy: UndefinedOr[ExpirationPolicyAlias]
    ) -> ExpirationConfig:
        ttl_days_ = get_defined_value(ttl_days, None)
        expiration_policy_raw = get_defined_value(expiration_policy, None)
        expiration_policy_: ExpirationPolicy | None = None
        if expiration_policy_raw is not None:
            expiration_policy_ = ExpirationPolicy.coerce(expiration_policy_raw)  # type: ignore[arg-type]

        return cls(
            ttl_days=ttl_days_,
            expiration_policy=expiration_policy_
        )

    def to_proto(self) -> ExpirationConfigProto | None:
        if not self.expiration_policy and not self.ttl_days:
            return None

        expiration_policy = 0
        if self.expiration_policy:
            expiration_policy = self.expiration_policy.to_proto()

        return ExpirationConfigProto(
            expiration_policy=expiration_policy,  # type: ignore[arg-type]
            ttl_days=self.ttl_days or 0
        )
