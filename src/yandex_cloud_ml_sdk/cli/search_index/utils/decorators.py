"""Decorators for CLI options that are shared across commands."""
from __future__ import annotations

import click

from ..constants import (
    DEFAULT_BATCH_SIZE, DEFAULT_CHUNK_OVERLAP_TOKENS, DEFAULT_INDEX_TYPE, DEFAULT_MAX_CHUNK_SIZE_TOKENS,
    DEFAULT_MAX_WORKERS, DEFAULT_SKIP_ON_ERROR
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
    Decorator to add search index configuration options.

    Adds:
    - --index-name: Name for the search index
    - --index-description: Description
    - --index-label: Labels (multiple)
    - --index-ttl-days: TTL in days
    - --index-expiration-policy: Expiration policy
    - --index-type: Index type (text/vector/hybrid)
    - --max-chunk-size-tokens: Chunk size
    - --chunk-overlap-tokens: Chunk overlap
    """
    func = click.option(
        "--index-name",
        help="Name for the search index",
    )(func)
    func = click.option(
        "--index-description",
        help="Description for the search index",
    )(func)
    func = click.option(
        "--index-label",
        "index_labels",
        multiple=True,
        help="Labels for the index in format KEY=VALUE (can be specified multiple times)",
    )(func)
    func = click.option(
        "--index-ttl-days",
        type=int,
        help="Time-to-live for the search index in days",
    )(func)
    func = click.option(
        "--index-expiration-policy",
        type=click.Choice(["static", "since_last_active"]),
        help="Expiration policy for the search index",
    )(func)
    func = click.option(
        "--index-type",
        type=click.Choice(["text", "vector", "hybrid"]),
        default=DEFAULT_INDEX_TYPE,
        show_default=True,
        help="Type of search index to create",
    )(func)
    func = click.option(
        "--max-chunk-size-tokens",
        type=int,
        default=DEFAULT_MAX_CHUNK_SIZE_TOKENS,
        show_default=True,
        help="Maximum chunk size in tokens (for text/hybrid indexes)",
    )(func)
    func = click.option(
        "--chunk-overlap-tokens",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP_TOKENS,
        show_default=True,
        help="Chunk overlap in tokens (for text/hybrid indexes)",
    )(func)
    return func


def file_options(func):
    """
    Decorator to add file upload configuration options.

    Adds:
    - --file-ttl-days: TTL for files
    - --file-expiration-policy: Expiration policy for files
    - --file-label: Labels for files (multiple)
    - --batch-size: Batch size for uploads
    - --max-concurrent-uploads: Number of concurrent uploads
    - --skip-on-error: Skip failed files
    """
    func = click.option(
        "--file-ttl-days",
        type=int,
        help="Time-to-live for uploaded files in days",
    )(func)
    func = click.option(
        "--file-expiration-policy",
        type=click.Choice(["static", "since_last_active"]),
        help="Expiration policy for uploaded files",
    )(func)
    func = click.option(
        "--file-label",
        "file_labels",
        multiple=True,
        help="Labels for files in format KEY=VALUE (can be specified multiple times)",
    )(func)
    func = click.option(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        show_default=True,
        help="Number of files to upload in each batch (currently unused)",
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
