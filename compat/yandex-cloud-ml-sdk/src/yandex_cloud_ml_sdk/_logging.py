from __future__ import annotations

import warnings
from logging import Handler, LogRecord, getLogger

from yandex_ai_studio_sdk._logging.utils import (
    DEFAULT_DATE_FORMAT, DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL, TRACE, LogLevel, setup_default_logging_impl
)

new_root = getLogger('yandex_cloud_ml_sdk')


def setup_default_logging(
    log_level: LogLevel = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
):
    setup_default_logging_impl(
        log_level=log_level,
        log_format=log_format,
        date_format=date_format,
        logger_name='yandex_cloud_ml_sdk'
    )


class RelayWithRenameHandler(Handler):
    def emit(self, record):
        new_record = LogRecord(
            name="yandex_cloud_ml_sdk" + record.name[len("yandex_ai_studio_sdk"):],
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            func=record.funcName,
            sinfo=record.stack_info
        )
        new_root.handle(new_record)


def setup_log_relay():
    logger = getLogger('yandex_ai_studio_sdk')
    logger.setLevel(TRACE)
    logger.addHandler(RelayWithRenameHandler())


def usage_warning():
    warnings.warn(
        "yandex-cloud-ml-sdk package is deprecated; "
        "use yandex-ai-studio-sdk package instead "
        "and refer to "
        "https://github.com/yandex-cloud/yandex-ai-studio-sdk/blob/master/compat/yandex-cloud-ml-sdk/MIGRATION.md",
        stacklevel=3
    )
