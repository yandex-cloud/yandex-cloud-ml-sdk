from __future__ import annotations

from pathlib import Path

import click

from ..file_sources import LocalFileSource
from ..file_sources.base import BaseFileSource
from ..utils import all_common_options, create_command_executor
from .base import BaseCommand


class LocalCommand(BaseCommand):
    """Command for creating search index from local filesystem files."""

    def __init__(
        self,
        # Local-specific options
        directory: Path,
        include_patterns: tuple[str, ...],
        exclude_patterns: tuple[str, ...],
        max_file_size: int | None,
        recursive: bool,
        # Common options
        **kwargs,
    ):
        """Initialize local command with local-specific and common parameters."""
        self.directory = directory
        self.include_patterns = include_patterns if include_patterns else ("**/*",)  # Default pattern if none specified
        self.exclude_patterns = exclude_patterns
        self.max_file_size = max_file_size
        self.recursive = recursive

        # Set default vector store name to directory name if not provided
        if not kwargs.get("name"):
            kwargs["name"] = directory.name

        # Initialize base command
        super().__init__(**kwargs)

    def create_file_source(self) -> BaseFileSource:
        """Create LocalFileSource with configured parameters."""
        return LocalFileSource(
            directory=self.directory,
            include_patterns=list(self.include_patterns),
            recursive=self.recursive,
            exclude_patterns=list(self.exclude_patterns) if self.exclude_patterns else None,
            max_file_size=self.max_file_size,
        )


@click.command(name="local")
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--pattern",
    "include_patterns",
    multiple=True,
    help="Glob pattern for matching files (e.g., '**/*.pdf' for all PDFs). Can be specified multiple times.",
)
@click.option(
    "--exclude-pattern",
    "exclude_patterns",
    multiple=True,
    help="Glob patterns to exclude (can be specified multiple times)",
)
@click.option(
    "--max-file-size",
    type=int,
    help="Maximum file size in bytes (larger files will be skipped)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    show_default=True,
    help="Whether to scan subdirectories recursively",
)
@all_common_options
def local_command(**kwargs):
    """
    Create a search index from local filesystem files.

    DIRECTORY is the path to scan for files.

    This command scans a local directory for files matching the specified
    pattern, uploads them to Yandex Cloud, and creates a search index.
    """
    create_command_executor(LocalCommand, **kwargs)
