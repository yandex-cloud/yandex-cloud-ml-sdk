from __future__ import annotations

import click

from ..file_sources.base import BaseFileSource
from ..file_sources.s3 import S3FileSource
from ..utils import all_common_options, create_command_executor
from .base import BaseCommand


class S3Command(BaseCommand):
    """Command for creating search index from S3-compatible storage."""

    def __init__(
        self,
        # S3-specific options
        bucket: str,
        prefix: str,
        endpoint_url: str | None,
        aws_access_key_id: str | None,
        aws_secret_access_key: str | None,
        region_name: str | None,
        include_patterns: tuple[str, ...],
        exclude_patterns: tuple[str, ...],
        max_file_size: int | None,
        # Common options
        **kwargs,
    ):
        """Initialize S3 command with S3-specific and common parameters."""
        self.bucket = bucket
        self.prefix = prefix
        self.endpoint_url = endpoint_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.max_file_size = max_file_size

        # Initialize base command
        super().__init__(**kwargs)

    def create_file_source(self) -> BaseFileSource:
        """Create S3FileSource with configured parameters."""
        return S3FileSource(
            bucket=self.bucket,
            prefix=self.prefix,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
            include_patterns=list(self.include_patterns) if self.include_patterns else None,
            exclude_patterns=list(self.exclude_patterns) if self.exclude_patterns else None,
            max_file_size=self.max_file_size,
        )


@click.command(name="s3")
@click.option(
    "--bucket",
    "-b",
    required=True,
    help="S3 bucket name",
)
@click.option(
    "--prefix",
    default="",
    show_default=True,
    help="Prefix (folder path) within the bucket",
)
@click.option(
    "--endpoint-url",
    help="Custom S3 endpoint URL (for S3-compatible services)",
)
@click.option(
    "--aws-access-key-id",
    envvar="AWS_ACCESS_KEY_ID",
    help="AWS access key ID (or use AWS_ACCESS_KEY_ID env var)",
)
@click.option(
    "--aws-secret-access-key",
    envvar="AWS_SECRET_ACCESS_KEY",
    help="AWS secret access key (or use AWS_SECRET_ACCESS_KEY env var)",
)
@click.option(
    "--region-name",
    envvar="AWS_DEFAULT_REGION",
    help="AWS region name (or use AWS_DEFAULT_REGION env var)",
)
@click.option(
    "--include-pattern",
    "include_patterns",
    multiple=True,
    help="Glob patterns to include (can be specified multiple times)",
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
@all_common_options
def s3_command(**kwargs):
    """
    Create a search index from S3-compatible storage.

    This command downloads files from an S3 bucket, uploads them to
    Yandex Cloud, and creates a search index.
    """
    create_command_executor(S3Command, **kwargs)
