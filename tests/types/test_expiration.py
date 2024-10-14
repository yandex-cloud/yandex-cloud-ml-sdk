from __future__ import annotations

import inspect

import pytest

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationConfigProto, ExpirationPolicy


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ('unspecified', ExpirationConfigProto.EXPIRATION_POLICY_UNSPECIFIED),
        ('static', ExpirationConfigProto.STATIC),
        ('since_last_active', ExpirationConfigProto.SINCE_LAST_ACTIVE),
        ('UNSPECIFIED', ExpirationConfigProto.EXPIRATION_POLICY_UNSPECIFIED),
        ('STATIC', ExpirationConfigProto.STATIC),
        ('SINCE_LAST_ACTIVE', ExpirationConfigProto.SINCE_LAST_ACTIVE),
        (0, ExpirationConfigProto.EXPIRATION_POLICY_UNSPECIFIED),
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
    "expected,test_input",
    [
        (ExpirationConfig(ttl_days=1, policy=None), 1),
        (ExpirationConfig(ttl_days=None, policy=ExpirationPolicy.STATIC), 'static'),
        (ExpirationConfig(ttl_days=None, policy=ExpirationPolicy.STATIC), 'STATIC'),
        (ValueError, 'foo'),
        (ExpirationConfig(ttl_days=123, policy=ExpirationPolicy.STATIC),
         ExpirationConfig(ttl_days=123, policy=ExpirationPolicy.STATIC)),
        (ExpirationConfig(ttl_days=None, policy=ExpirationPolicy.SINCE_LAST_ACTIVE), ExpirationPolicy.SINCE_LAST_ACTIVE),
        (ExpirationConfig(ttl_days=2, policy=ExpirationPolicy.STATIC), {'ttl_days': 2, 'policy': 'static'}),
        (ExpirationConfig(ttl_days=None, policy=ExpirationPolicy.STATIC), {'policy': 'static'}),
        (ExpirationConfig(ttl_days=2, policy=None), {'ttl_days': 2}),
        (ExpirationConfig(ttl_days=None, policy=None), {}),
        (ExpirationConfig(ttl_days=None, policy=None), None),
        (TypeError, int),

    ]
)
def test_expiration_config(expected, test_input):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            ExpirationConfig.coerce(test_input)
    else:
        assert ExpirationConfig.coerce(test_input) == expected
