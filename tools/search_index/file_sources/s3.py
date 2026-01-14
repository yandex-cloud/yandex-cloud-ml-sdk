from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from .base import BaseFileSource, FileMetadata


class S3FileSource(BaseFileSource):
    """Source for loading files from S3-compatible storage."""

    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "",
        endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        max_file_size: int | None = None,
    ):
        """
        Initialize S3 file source.

        Args:
            bucket: S3 bucket name
            prefix: Prefix (folder path) within the bucket
            endpoint_url: Custom S3 endpoint URL (for S3-compatible services)
            aws_access_key_id: AWS access key ID (or from env)
            aws_secret_access_key: AWS secret access key (or from env)
            region_name: AWS region name
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            max_file_size: Maximum file size in bytes
        """
        self.bucket = bucket
        self.prefix = prefix
        self.endpoint_url = endpoint_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size = max_file_size

    def list_files(self) -> Iterator[FileMetadata]:
        """List all files in the S3 bucket matching the patterns."""
        # TODO: Implement S3 file listing using boto3
        raise NotImplementedError

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Download file content from S3."""
        # TODO: Implement S3 file download using boto3
        raise NotImplementedError

    def get_file_count_estimate(self) -> int | None:
        """Get count of files in S3 bucket."""
        # TODO: Implement S3 counting logic
        raise NotImplementedError
