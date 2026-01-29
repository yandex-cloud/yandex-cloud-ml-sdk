from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from .base import BaseFileSource, FileMetadata

logger = logging.getLogger(__name__)


class LocalFileSource(BaseFileSource):
    """Source for loading files from local filesystem."""

    def __init__(
        self,
        directory: Path | str,
        *,
        include_patterns: list[str] | None = None,
        recursive: bool = True,
        exclude_patterns: list[str] | None = None,
        max_file_size: int | None = None,
    ):
        """
        Initialize local file source.

        Args:
            directory: Root directory to scan for files
            include_patterns: List of glob patterns for matching files (e.g., ["**/*.md", "**/*.txt"])
                              If None or empty, defaults to ["**/*"] (all files)
            recursive: Whether to scan subdirectories recursively
            exclude_patterns: List of glob patterns to exclude
            max_file_size: Maximum file size in bytes (files larger will be skipped)
        """
        self.directory = Path(directory)
        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {self.directory}")
        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory}")

        self.include_patterns = include_patterns if include_patterns else ["**/*"]
        self.recursive = recursive
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size = max_file_size

    def list_files(self) -> Iterator[FileMetadata]:
        """List all files matching the include patterns in the directory."""
        logger.info("Scanning directory: %s with patterns: %s", self.directory, self.include_patterns)

        # Collect all unique files matching any pattern
        seen_files = set()

        for pattern in self.include_patterns:
            logger.debug("Applying pattern: %s", pattern)
            for file_path in self.directory.glob(pattern):
                if not file_path.is_file():
                    continue

                # Skip if already processed
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)

                if self._is_excluded(file_path):
                    logger.debug("Skipping excluded file: %s", file_path)
                    continue

                try:
                    file_size = file_path.stat().st_size
                    if self.max_file_size and file_size > self.max_file_size:
                        logger.warning(
                            "Skipping file (too large): %s (%d bytes > %d max)",
                            file_path,
                            file_size,
                            self.max_file_size,
                        )
                        continue
                except OSError as e:
                    logger.error("Cannot access file: %s - %s", file_path, e)
                    continue

                metadata = FileMetadata(
                    path=file_path,
                    name=file_path.name,
                    mime_type=None,
                )

                yield metadata

        logger.info("Finished scanning with %d unique files found", len(seen_files))

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Read file content from the local filesystem."""
        file_path = Path(file_metadata.path)
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except OSError as e:
            logger.error("Failed to read file: %s - %s", file_path, e)
            raise

    def get_file_count_estimate(self) -> int | None:
        """Count files matching the include patterns."""
        try:
            seen_files = set()
            for pattern in self.include_patterns:
                for file_path in self.directory.glob(pattern):
                    if file_path.is_file() and not self._is_excluded(file_path):
                        seen_files.add(file_path)

            count = len(seen_files)
            logger.info("Found %d files matching patterns", count)
            return count
        except Exception as e:
            logger.warning("Failed to count files: %s", e)
            return None

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file matches any exclusion pattern."""
        relative_path = file_path.relative_to(self.directory)

        for exclude_pattern in self.exclude_patterns:
            if relative_path.match(exclude_pattern):
                return True

        return False
