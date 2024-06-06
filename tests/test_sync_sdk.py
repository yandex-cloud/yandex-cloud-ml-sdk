from __future__ import annotations

import inspect

from yandex_cloud_ml_sdk._types.function import BaseFunction
from yandex_cloud_ml_sdk._types.operation import Operation


def check_object_is_sync(obj):
    for attr_name in dir(obj):
        if attr_name.startswith('_'):
            continue

        value = getattr(obj, attr_name)
        assert not inspect.iscoroutinefunction(value)
        assert not inspect.isasyncgenfunction(value)


def test_models_are_sync(sdk):
    """
    Test about us not forget to wrap model method in run_async
    """
    resource_dict = sdk.models.__dict__

    for value in resource_dict.values():
        if isinstance(value, BaseFunction):
            function = value

            model = function('test://test')
            check_object_is_sync(model)


def test_operation_is_sync():
    check_object_is_sync(Operation)
