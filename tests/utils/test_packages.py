from __future__ import annotations

import importlib.metadata

import pytest

from yandex_cloud_ml_sdk._utils.packages import requires_package


@requires_package('somerandomname', '>1', 'mysupermethod')
def mysupermethod():
    pass


@requires_package('yandexcloud', '<0.100', 'mysupermethod')
def mysupermethod2():
    pass


@requires_package('yandexcloud', '>0.100', 'mysupermethod')
def mysupermethod3():
    pass


def test_requires_package():
    with pytest.raises(RuntimeError) as exc_info:
        mysupermethod()
    assert exc_info.value.args[0] == (
        '"mysupermethod" requires package "somerandomname>1"'
        ' to be installed, but you don\'t have any version installed'
    )
    assert str(exc_info.traceback[0].path) == __file__
    assert str(exc_info.traceback[-1].path) == __file__

    installed_version = importlib.metadata.version('yandexcloud')
    with pytest.raises(
        RuntimeError,
        match=(
            '"mysupermethod" requires package "yandexcloud<0.100" to be installed, '
            f'but you have "{installed_version}" installed'
        )
    ):
        mysupermethod2()

    mysupermethod3()
