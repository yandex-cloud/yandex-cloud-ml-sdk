from __future__ import annotations

import pytest

from yandex_cloud_ml_sdk import AsyncYCloudML, YCloudML
from yandex_cloud_ml_sdk._testing.interceptor import (
    AsyncUnaryStreamClientInterceptor, AsyncUnaryUnaryClientInterceptor, CassetteManager
)

pytest_plugins = ['pytest_recording', 'yandex_cloud_ml_sdk._testing.plugin']


@pytest.fixture(name='interceptors')
def fixture_interceptors(request):
    cassette_manager = CassetteManager(request)
    return [
        AsyncUnaryUnaryClientInterceptor(cassette_manager),
        AsyncUnaryStreamClientInterceptor(cassette_manager),
    ]


@pytest.fixture(name='folder_id')
def fixture_folder_id():
    return 'b1ghsjum2v37c2un8h64'


@pytest.fixture
def sdk(folder_id, interceptors):
    return YCloudML(folder_id=folder_id, interceptors=interceptors)


@pytest.fixture
def async_sdk(folder_id, interceptors):
    return AsyncYCloudML(folder_id=folder_id, interceptors=interceptors)
