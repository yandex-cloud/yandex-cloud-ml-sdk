from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from yandex_cloud_ml_sdk._logging import get_logger

logger = get_logger(__name__)

HTTPServiceName = Literal['http_completions']

CLOUD_ENDPOINTS: dict[str, dict[HTTPServiceName, str]] = {
    'api.cloud.yandex.net': {
        'http_completions': 'https://llm.api.cloud.yandex.net/v1/'
    },
    'api.cloud-preprod.yandex.net': {
        'http_completions': 'https://llm-api.ml.cloud-preprod.yandex.net/v1/'
    }
}


def get_host(url: str) -> str:
    """
    >>> get_host('foo.bar')
    'foo.bar'
    >>> get_host('https://foo.bar')
    'foo.bar'
    >>> get_host('foo.bar:8000')
    'foo.bar'
    """

    if '://' not in url:
        url = 'http://' + url
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise RuntimeError(f'failed to parse a host from {url}')
    return host


@lru_cache(maxsize=None)
def get_http_service_endpoint(cloud_endpoint: str, service: HTTPServiceName) -> str:
    cloud_host = get_host(cloud_endpoint)
    endpoints = CLOUD_ENDPOINTS.get(cloud_host)
    if not endpoints:
        raise RuntimeError(
            f'service {service} is unavailable for service endpoints discovery '
            f'with cloud endpoint {cloud_endpoint}'
        )

    return endpoints[service]
