from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from ..commands.base import BaseCommand


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


def create_command_executor(command_class: type[BaseCommand], **kwargs: Any) -> None:
    """
    Create and execute a command.

    This is a convenience function for command entry points.

    Args:
        command_class: The command class to instantiate (must be a subclass of BaseCommand)
        **kwargs: All parameters to pass to the command constructor
    """
    command = command_class(**kwargs)
    command.execute()
