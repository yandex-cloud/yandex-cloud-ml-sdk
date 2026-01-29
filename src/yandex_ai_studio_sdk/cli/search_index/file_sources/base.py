from __future__ import annotations

import abc
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileMetadata:
    """Metadata about a file to be uploaded."""

    path: Path | str
    """Path or identifier of the file"""

    name: str | None = None
    """Display name for the file"""

    mime_type: str | None = None
    """MIME type of the file"""

    labels: dict[str, str] | None = None
    """Labels to attach to the file"""

    description: str | None = None
    """Description of the file"""


class BaseFileSource(abc.ABC):
    """
    Base class for file sources that can provide files for indexing.
    """

    @abc.abstractmethod
    def list_files(self) -> Iterator[FileMetadata]:
        """
        List all files available from this source.

        Yields:
            FileMetadata objects for each file
        """

    @abc.abstractmethod
    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """
        Retrieve the content of a specific file.

        Args:
            file_metadata: Metadata about the file to retrieve
        """

    @abc.abstractmethod
    def get_file_count_estimate(self) -> int | None:
        """Get an estimate of the number of files (if available)."""
