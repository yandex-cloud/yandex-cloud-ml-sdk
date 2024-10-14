from __future__ import annotations

import inspect

import pytest

from yandex_cloud_ml_sdk._types.expiration import ExpirationConfig, ExpirationConfigProto, ExpirationPolicy


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
    "expected,expected_strict,test_input",
    [
        (ExpirationConfig(ttl_days=1), ValueError, 1),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.STATIC), ValueError, 'static'),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.STATIC), ValueError, 'STATIC'),
        (ValueError, ValueError, 'foo'),
        (ExpirationConfig(ttl_days=123, expiration_policy=ExpirationPolicy.STATIC),
         ExpirationConfig(ttl_days=123, expiration_policy=ExpirationPolicy.STATIC),
         ExpirationConfig(ttl_days=123, expiration_policy=ExpirationPolicy.STATIC)),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.SINCE_LAST_ACTIVE), ValueError, ExpirationPolicy.SINCE_LAST_ACTIVE),
        (ExpirationConfig(ttl_days=2, expiration_policy=ExpirationPolicy.STATIC),
         ExpirationConfig(ttl_days=2, expiration_policy=ExpirationPolicy.STATIC),
         {'ttl_days': 2, 'expiration_policy': 'static'}),
        (ExpirationConfig(expiration_policy=ExpirationPolicy.STATIC), ValueError, {'expiration_policy': 'static'}),
        (ExpirationConfig(ttl_days=2), ValueError, {'ttl_days': 2}),
        (ExpirationConfig(), ExpirationConfig(), {}),
        (ExpirationConfig(), ExpirationConfig(), None),
        (TypeError, TypeError, int),

    ],
)
def test_expiration_config(expected, expected_strict, test_input):
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            ExpirationConfig.coerce(test_input)
    else:
        assert ExpirationConfig.coerce(test_input) == expected

    if inspect.isclass(expected_strict) and issubclass(expected_strict, Exception):
        with pytest.raises(expected_strict):
            ExpirationConfig.coerce_strict(test_input)
    else:
        assert ExpirationConfig.coerce_strict(test_input) == expected_strict
