from __future__ import annotations

import fnmatch
import logging
from collections.abc import Iterator
from pathlib import Path

import boto3  # type: ignore[import-untyped]

from .base import BaseFileSource, FileMetadata

logger = logging.getLogger(__name__)


class S3FileSource(BaseFileSource):
    """Source for loading files from S3-compatible storage."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        max_file_size: int | None = None,
    ):
        """Initialize S3 file source.

        Args:
            bucket: S3 bucket name
            prefix: Prefix (folder path) within the bucket
            endpoint_url: Custom S3 endpoint URL for S3-compatible services
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
            include_patterns: Glob patterns to include (e.g., ["*.pdf", "*.txt"])
            exclude_patterns: Glob patterns to exclude
            max_file_size: Maximum file size in bytes
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size = max_file_size

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        logger.info("S3FileSource initialized for s3://%s/%s", bucket, prefix or "(root)")

    def _get_relative_key(self, key: str) -> str:
        """Get key relative to prefix."""
        if not self.prefix:
            return key
        return key[len(self.prefix):].lstrip("/")

    def _should_include(self, key: str, size: int) -> bool:
        """Check if file should be included based on patterns and size."""
        # Skip directories
        if key.endswith("/"):
            return False

        # Check size limit
        if self.max_file_size and size > self.max_file_size:
            return False

        # Check patterns
        relative_key = self._get_relative_key(key)
        return self._matches_patterns(relative_key)

    def _matches_patterns(self, relative_path: str) -> bool:
        """Check if file path matches include/exclude patterns using fnmatch."""
        # If include patterns specified, file must match at least one
        if self.include_patterns:
            if not any(fnmatch.fnmatch(relative_path, pattern) for pattern in self.include_patterns):
                return False

        # If exclude patterns specified, file must not match any
        if self.exclude_patterns:
            if any(fnmatch.fnmatch(relative_path, pattern) for pattern in self.exclude_patterns):
                return False

        return True

    def _iter_objects(self):
        """Iterate over all objects in bucket with prefix."""
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=self.bucket, Prefix=self.prefix)

        for page in page_iterator:
            if "Contents" in page:
                yield from page["Contents"]

    def list_files(self) -> Iterator[FileMetadata]:
        """List files in S3 bucket using pagination."""
        logger.info("Listing files in s3://%s/%s", self.bucket, self.prefix)

        file_count = 0
        for obj in self._iter_objects():
            key = obj["Key"]
            size = obj["Size"]

            if self._should_include(key, size):
                yield FileMetadata(
                    path=key,
                    name=Path(key).name,
                    mime_type=None,
                )
                file_count += 1

        logger.info("Found %d files matching patterns", file_count)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Download file content from S3."""
        key = str(file_metadata.path)
        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def get_file_count_estimate(self) -> int | None:
        """Count files matching patterns by paginating through all objects."""
        try:
            return sum(1 for obj in self._iter_objects() if self._should_include(obj["Key"], obj["Size"]))
        except Exception as e:
            logger.warning("Failed to count files: %s", e)
            return None
