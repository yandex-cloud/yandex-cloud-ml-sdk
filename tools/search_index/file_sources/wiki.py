from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from .base import BaseFileSource, FileMetadata


class WikiFileSource(BaseFileSource):
    """Source for loading pages from MediaWiki instances."""

    def __init__(
        self,
        api_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        category: str | None = None,
        namespace: int | None = None,
        page_titles: list[str] | None = None,
        export_format: str = "pdf",
    ):
        """
        Initialize MediaWiki file source.

        Args:
            api_url: MediaWiki API URL (e.g., https://en.wikipedia.org/w/api.php)
            username: Wiki username (if authentication required)
            password: Wiki password (if authentication required)
            category: Export all pages from this category
            namespace: MediaWiki namespace to export from
            page_titles: Specific page titles to export
            export_format: Format for exporting pages ('pdf', 'html', 'markdown')
        """
        self.api_url = api_url
        self.username = username
        self.password = password
        self.category = category
        self.namespace = namespace
        self.page_titles = page_titles or []
        self.export_format = export_format

    def list_files(self) -> Iterator[FileMetadata]:
        """List all pages from the MediaWiki instance."""
        # TODO: Implement MediaWiki API integration
        raise NotImplementedError

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Download page content from MediaWiki."""
        # TODO: Implement MediaWiki content export
        raise NotImplementedError

    def get_file_count_estimate(self) -> int | None:
        """Get count of pages in MediaWiki category/namespace."""
        # TODO: Implement MediaWiki counting logic
        raise NotImplementedError
