from __future__ import annotations

from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "allow_grpc: Mark the test as allowed to use grpc")


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("yandex-cloud-ml-sdk")
    group.addoption(
        "--regenerate-grpc",
        action="store_true",
        default=False,
        help="Regenerate cassettes with grpc requests",
    )
