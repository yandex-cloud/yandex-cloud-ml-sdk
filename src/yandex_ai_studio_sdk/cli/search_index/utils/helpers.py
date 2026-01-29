from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from yandex_ai_studio_sdk.cli.search_index.config import (
    ConfigLoader, add_default_values, extract_source_config, filter_null_values, merge_config_with_cli_args,
    normalize_config_keys, normalize_list_params, parse_auth_config
)

if TYPE_CHECKING:
    from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand

logger = logging.getLogger(__name__)


def validate_authentication(
    username: str | None,
    token: str | None,
    auth_type: str = "authentication",
) -> tuple[str, str]:
    """
    Validate that authentication credentials are provided.

    Args:
        username: Username or None
        token: API token/password or None
        auth_type: Type of authentication (for error messages)
    """
    if not username or not token:
        raise click.ClickException(
            f"{auth_type} required. Provide credentials via command line options or environment variables."
        )

    return username, token


def _get_source_name_from_command_class(command_class: type[BaseCommand]) -> str:
    """Map command class to source name."""
    class_name = command_class.__name__.lower()
    if "local" in class_name:
        return "local"
    elif "s3" in class_name:
        return "s3"
    elif "wiki" in class_name:
        return "wiki"
    elif "confluence" in class_name:
        return "confluence"
    else:
        return "unknown"


def create_command_executor(command_class: type[BaseCommand], **kwargs: Any) -> None:
    """
    Create and execute a command.

    Handles config file loading and merging with CLI args.

    Args:
        command_class: The command class to instantiate (must be a subclass of BaseCommand)
        **kwargs: All parameters to pass to the command constructor
    """
    config_path: Path | None = kwargs.pop("config", None)

    if config_path:
        source_name = _get_source_name_from_command_class(command_class)

        config = ConfigLoader.load(config_path)
        config = normalize_config_keys(config)
        config = extract_source_config(config, source_name)
        config = filter_null_values(config)
        config = normalize_list_params(config)
        config = add_default_values(config, source_name)
        config = parse_auth_config(config)
        kwargs = merge_config_with_cli_args(config, kwargs)
        logger.info("Loaded configuration from %s (source: %s)", config_path, source_name)

    command = command_class(**kwargs)
    command.execute()
