from __future__ import annotations

import inspect

import pytest

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationConfigProto, ExpirationPolicy
from yandex_cloud_ml_sdk._types.misc import UNDEFINED


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ('static', ExpirationConfigProto.STATIC),
        ('since_last_active', ExpirationConfigProto.SINCE_LAST_ACTIVE),
        ('STATIC', ExpirationConfigProto.STATIC),
        ('SINCE_LAST_ACTIVE', ExpirationConfigProto.SINCE_LAST_ACTIVE),
        (1, ExpirationConfigProto.STATIC),
        (2, ExpirationConfigProto.SINCE_LAST_ACTIVE),
        (3, ValueError),
        ('foo', ValueError),
        ({}, TypeError),
    ]
)
def test_expiration_policy(test_input, expected):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            ExpirationPolicy.coerce(test_input)
    else:
        assert ExpirationPolicy.coerce(test_input).to_proto() == expected


@pytest.mark.parametrize(
    "expected,ttl_days,expiration_policy",
    [
        (ExpirationConfig(ttl_days=1), 1, UNDEFINED),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.STATIC), UNDEFINED, 'static'),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.STATIC), UNDEFINED, 'STATIC'),
        (ValueError, UNDEFINED, 'foo'),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.SINCE_LAST_ACTIVE),
         UNDEFINED, ExpirationPolicy.SINCE_LAST_ACTIVE),
        (ExpirationConfig(ttl_days=2, expiration_policy=ExpirationPolicy.STATIC), 2, 'static'),
        (ExpirationConfig(), UNDEFINED, UNDEFINED),
        (TypeError, str, int),

    ],
)
def test_expiration_config(expected, ttl_days, expiration_policy):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy)
    else:
        assert ExpirationConfig.coerce(ttl_days=ttl_days, expiration_policy=expiration_policy) == expected
