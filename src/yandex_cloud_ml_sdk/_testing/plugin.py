from __future__ import annotations

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "allow_grpc: Mark the test as allowed to use grpc")
    config.addinivalue_line("markers", "heavy: Mark the test as heavy")


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("yandex-cloud-ml-sdk")

    group.addoption(
        '--generate-grpc',
        action="store_true",
        default=False,
        help="Generate cassettes with grpc requests",
    )

    group.addoption(
        "--regenerate-grpc",
        action="store_true",
        default=False,
        help="Regenerate cassettes with grpc requests",
    )

    group.addoption(
        "--heavy",
        action="store_true",
        default=False,
        help="Regenerate cassettes with grpc requests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--heavy"):
        return

    skip_heavy = pytest.mark.skip(reason="need --heavy option to run")
    for item in items:
        if "heavy" in item.keywords:
            item.add_marker(skip_heavy)
