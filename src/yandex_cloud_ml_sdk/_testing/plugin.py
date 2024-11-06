from __future__ import annotations

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "allow_grpc: Mark the test as allowed to use grpc")
    config.addinivalue_line("markers", "require_env: Mark the test is requires some env")


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
        help="Run tests with a mark 'heavy'",
    )

    group.addoption(
        "--env",
        action="extend",
        default=[],
        nargs="*",
        help="Run tests that requires specific env to run",
    )


def pytest_collection_modifyitems(config, items):
    run_heavy = config.getoption("--heavy")
    envs = frozenset(config.getoption("--env"))

    skip_heavy = pytest.mark.skip(reason="need --heavy option to run")
    for item in items:
        if "heavy" in item.keywords:
            if not run_heavy:
                item.add_marker(skip_heavy)

        env_marks = frozenset().union(
            *(m.args for m in item.iter_markers('require_env'))
        )

        if not env_marks.issubset(envs):
            missing = ', '.join(env_marks - envs)
            skip_env = pytest.mark.skip(reason=f"requires specific --env: {missing}")
            item.add_marker(skip_env)
