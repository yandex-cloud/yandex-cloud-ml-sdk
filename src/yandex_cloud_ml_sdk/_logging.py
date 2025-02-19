from __future__ import annotations

import logging
import os
import typing

from google.protobuf.message import Message

from ._utils.proto import proto_to_dict

UpperLogLevel = typing.Literal['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'TRACE']
LogLevel = typing.Union[
    UpperLogLevel,
    typing.Literal['critical', 'fatal', 'error', 'warn', 'warning', 'info', 'debug', 'TRACE'],
    int
]
LOG_LEVEL_ENV_VARS = ("YC_LOG_LEVEL", )
DEFAULT_LOG_LEVEL: typing.Final = "INFO"
DEFAULT_LOG_FORMAT = "[%(levelname)1.1s %(asctime)s %(name)s:%(lineno)d] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
TRACE = 5


def setup_default_logging(
    log_level: LogLevel = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str= DEFAULT_DATE_FORMAT,
) -> None:
    if isinstance(log_level, str):
        log_level = typing.cast(UpperLogLevel, log_level.upper())

        if log_level == 'TRACE':
            log_level = TRACE

    logger = logging.getLogger('yandex_cloud_ml_sdk')
    if logger.handlers:
        return

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format,
        style="%"
    )
    handler.setFormatter(formatter)
    logger.setLevel(log_level)
    logger.addHandler(handler)


def setup_default_logging_from_env() -> None:
    level_name: str | int | None
    for env_name in LOG_LEVEL_ENV_VARS:
        if level_name := os.getenv(env_name):
            if level_name.isdigit():
                level_name = int(level_name)
            # I can ignore arg-type here because anyway underlying logging code
            # will validate level_name anyway
            setup_default_logging(level_name)  # type: ignore[arg-type]
            return


class ProtobufMessageFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        args = record.args or ()
        if any(isinstance(arg, Message) for arg in args):
            record.args = tuple(
                dict(proto_to_dict(arg)) if isinstance(arg, Message) else arg
                for arg in args
            )

        return record


PROTO_FILTER = ProtobufMessageFilter()

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addFilter(PROTO_FILTER)
    return logger
