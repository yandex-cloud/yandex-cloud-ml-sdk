from __future__ import annotations

import fnmatch
import logging
from collections.abc import Iterator
from pathlib import Path

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

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
        """Initialize S3 file source and test connection.

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
        self.prefix = prefix.rstrip("/")  # Remove trailing slash
        self.endpoint_url = endpoint_url
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size = max_file_size

        # Create S3 client
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )
            logger.info(
                "S3 client initialized for bucket '%s' (endpoint: %s)",
                bucket,
                endpoint_url or "default AWS",
            )
            # Test connection
            self._test_connection()
        except Exception as e:
            raise ValueError(f"Failed to initialize S3 client: {e}") from e

    def _test_connection(self) -> None:
        """Test S3 connection by checking if bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info("Successfully connected to bucket '%s'", self.bucket)
        except ClientError as e:
            raise ValueError(f"Error accessing bucket '{self.bucket}': {e}") from e

    def list_files(self) -> Iterator[FileMetadata]:
        """List files in S3 bucket using pagination to avoid loading all objects into memory.

        Yields:
            FileMetadata for each matching file
        """
        logger.info("Listing files in s3://%s/%s", self.bucket, self.prefix)

        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket,
            Prefix=self.prefix,
        )

        prefix_len = len(self.prefix) if self.prefix else 0
        file_count = 0

        for page in page_iterator:
            if "Contents" not in page:
                logger.warning("No objects found with prefix '%s'", self.prefix)
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                size = obj["Size"]

                if key.endswith("/"):
                    continue

                relative_key = key[prefix_len:].lstrip("/") if prefix_len else key

                if not self._matches_patterns(relative_key):
                    logger.debug("Skipping file (pattern mismatch): %s", key)
                    continue

                if self.max_file_size and size > self.max_file_size:
                    logger.warning(
                        "Skipping file (too large): %s (%d bytes > %d max)",
                        key,
                        size,
                        self.max_file_size,
                    )
                    continue

                # Extract filename
                filename = Path(key).name

                metadata = FileMetadata(
                    path=key,  # Use S3 key as path
                    name=filename,
                    mime_type=None,  # Let SDK auto-detect MIME type
                    labels={
                        "source": "s3",
                        "bucket": self.bucket,
                        "prefix": self.prefix,
                    },
                )

                file_count += 1
                logger.debug("Found file: %s (size: %d)", key, size)
                yield metadata

        logger.info("Found %d files matching patterns", file_count)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Download file content from S3.

        Args:
            file_metadata: File metadata with S3 key in path field
        """
        key = str(file_metadata.path)

        try:
            logger.debug("Downloading file from s3://%s/%s", self.bucket, key)
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)

            content = response["Body"].read()

            logger.debug("Downloaded %d bytes from %s", len(content), key)
            return content

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error("Failed to download file %s: %s", key, error_code)
            raise
        except Exception as e:
            logger.error("Failed to download file %s: %s", key, e)
            raise

    def get_file_count_estimate(self) -> int | None:
        """Count files matching patterns by paginating through all objects.
        """
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=self.prefix,
            )

            prefix_len = len(self.prefix) if self.prefix else 0
            count = 0

            for page in page_iterator:
                if "Contents" not in page:
                    break

                for obj in page["Contents"]:
                    key = obj["Key"]
                    size = obj.get("Size", 0)

                    if key.endswith("/"):
                        continue

                    relative_key = key[prefix_len:].lstrip("/") if prefix_len else key

                    if self._matches_patterns(relative_key):
                        if not self.max_file_size or size <= self.max_file_size:
                            count += 1

            logger.info("Estimated %d files in bucket", count)
            return count

        except Exception as e:
            logger.warning("Failed to count files: %s", e)
            return None

    def _matches_patterns(self, relative_path: str) -> bool:
        """Check if file path matches include/exclude patterns using fnmatch.

        Args:
            relative_path: Path relative to bucket prefix
        """
        # If include patterns specified, file must match at least one
        if self.include_patterns:
            matches_include = any(
                fnmatch.fnmatch(relative_path, pattern)
                for pattern in self.include_patterns
            )
            if not matches_include:
                return False

        # If exclude patterns specified, file must not match any
        if self.exclude_patterns:
            matches_exclude = any(
                fnmatch.fnmatch(relative_path, pattern)
                for pattern in self.exclude_patterns
            )
            if matches_exclude:
                return False

        return True
