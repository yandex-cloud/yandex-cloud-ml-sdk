from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from .base import BaseFileSource, FileMetadata


class ConfluenceFileSource(BaseFileSource):
    """Source for loading pages/attachments from Atlassian Confluence."""

    def __init__(
        self,
        url: str,
        *,
        username: str | None = None,
        api_token: str | None = None,
        space_key: str | None = None,
        page_ids: list[str] | None = None,
        include_attachments: bool = True,
        export_format: str = "pdf",
    ):
        """
        Initialize Confluence file source.

        Args:
            url: Confluence instance URL (e.g., https://your-domain.atlassian.net/wiki)
            username: Confluence username (email)
            api_token: Confluence API token
            space_key: Confluence space key to export (optional)
            page_ids: Specific page IDs to export (optional)
            include_attachments: Whether to include page attachments
            export_format: Format for exporting pages ('pdf', 'html', 'markdown')
        """
        self.url = url
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.page_ids = page_ids or []
        self.include_attachments = include_attachments
        self.export_format = export_format

    def list_files(self) -> Iterator[FileMetadata]:
        """List all pages and attachments from Confluence."""
        # TODO: Implement Confluence API integration
        raise NotImplementedError

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Download page or attachment content from Confluence."""
        # TODO: Implement Confluence content export
        raise NotImplementedError

    def get_file_count_estimate(self) -> int | None:
        """Get count of pages/attachments in Confluence space."""
        # TODO: Implement Confluence counting logic
        raise NotImplementedError
