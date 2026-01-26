"""Decorators for CLI options that are shared across commands."""
from __future__ import annotations

import click

from ..constants import (
    DEFAULT_CHUNK_OVERLAP_TOKENS, DEFAULT_MAX_CHUNK_SIZE_TOKENS, DEFAULT_MAX_WORKERS, DEFAULT_SKIP_ON_ERROR
)


def common_options(func):
    """
    Decorator to add common options to all subcommands.

    Adds:
    - --folder-id: Yandex Cloud folder ID
    - --auth: Authentication token
    - --endpoint: Custom API endpoint
    - -v/--verbose: Verbosity level
    - --format: Output format (text or json)
    """
    func = click.option(
        "--folder-id",
        envvar="YC_FOLDER_ID",
        help="Yandex Cloud folder ID (can also use YC_FOLDER_ID env var)",
    )(func)
    func = click.option(
        "--auth",
        envvar="YC_API_KEY",
        help="Authentication token (can also use YC_API_KEY, YC_IAM_TOKEN, etc.)",
    )(func)
    func = click.option(
        "--endpoint",
        help="Custom API endpoint",
    )(func)
    func = click.option(
        "-v",
        "--verbose",
        count=True,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )(func)
    func = click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
        help="Output format (text for human-readable, json for machine-readable)",
    )(func)
    return func


def index_options(func):
    """
    Decorator to add vector store configuration options (OpenAI-compatible).

    Adds:
    - --name: Name for the vector store
    - --metadata: Metadata key-value pairs (multiple)
    - --expires-after-days: TTL in days
    - --expires-after-anchor: Expiration anchor point
    - --max-chunk-size-tokens: Chunk size
    - --chunk-overlap-tokens: Chunk overlap
    """
    func = click.option(
        "--name",
        help="Name for the vector store",
    )(func)
    func = click.option(
        "--metadata",
        "metadata",
        multiple=True,
        help="Metadata for the vector store in format KEY=VALUE (can be specified multiple times, max 16 pairs)",
    )(func)
    func = click.option(
        "--expires-after-days",
        type=int,
        help="Time-to-live for the vector store in days",
    )(func)
    func = click.option(
        "--expires-after-anchor",
        type=click.Choice(["created_at", "last_active_at"]),
        help="When to start counting expiration: 'created_at' or 'last_active_at'",
    )(func)
    func = click.option(
        "--max-chunk-size-tokens",
        type=int,
        default=DEFAULT_MAX_CHUNK_SIZE_TOKENS,
        show_default=True,
        help="Maximum chunk size in tokens for chunking strategy",
    )(func)
    func = click.option(
        "--chunk-overlap-tokens",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP_TOKENS,
        show_default=True,
        help="Chunk overlap in tokens for chunking strategy",
    )(func)
    return func


def file_options(func):
    """
    Decorator to add file upload configuration options (OpenAI-compatible).

    Adds:
    - --file-purpose: Purpose of the file
    - --file-expires-after-seconds: TTL for files in seconds
    - --file-expires-after-anchor: Expiration anchor for files
    - --max-concurrent-uploads: Number of concurrent uploads
    - --skip-on-error: Skip failed files

    Note: MIME types are auto-detected by the server, no need to specify.
    """
    func = click.option(
        "--file-purpose",
        default="assistants",
        show_default=True,
        help="Purpose of the file (always 'assistants' for vector stores)",
    )(func)
    func = click.option(
        "--file-expires-after-seconds",
        type=int,
        help="Time-to-live for uploaded files in seconds",
    )(func)
    func = click.option(
        "--file-expires-after-anchor",
        type=click.Choice(["created_at", "last_active_at"]),
        help="When to start counting file expiration: 'created_at' or 'last_active_at'",
    )(func)
    func = click.option(
        "--max-concurrent-uploads",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        show_default=True,
        help="Maximum number of concurrent upload tasks",
    )(func)
    func = click.option(
        "--skip-on-error",
        is_flag=True,
        default=DEFAULT_SKIP_ON_ERROR,
        show_default=True,
        help="Skip files that fail to upload instead of stopping",
    )(func)
    return func


def all_common_options(func):
    """
    Convenience decorator that applies all common option decorators.

    This combines common_options, index_options, and file_options.
    """
    func = file_options(func)
    func = index_options(func)
    func = common_options(func)
    return func
