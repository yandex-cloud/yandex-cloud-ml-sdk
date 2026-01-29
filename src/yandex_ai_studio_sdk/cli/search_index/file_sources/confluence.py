from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from urllib.parse import parse_qs, urlparse

from atlassian import Confluence  # type: ignore[import-untyped]

from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource, FileMetadata

logger = logging.getLogger(__name__)


class ConfluenceFileSource(BaseFileSource):
    """Source for loading page content from Atlassian Confluence."""

    def __init__(
        self,
        page_urls: list[str],
        base_url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
        *,
        export_format: str = "pdf",
    ):
        if not page_urls:
            raise ValueError("At least one page URL must be provided")

        self.page_urls = page_urls
        self.export_format = export_format

        # Determine base URL
        if base_url:
            self.url = base_url.rstrip('/')
            # Validate all URLs start with this base
            for page_url in page_urls:
                if not page_url.startswith(self.url):
                    raise ValueError(f"Page URL {page_url} does not start with base URL {self.url}")
        else:
            # Extract from first URL
            self.url = self._extract_base_url(page_urls[0])
            logger.info("Extracted base URL: %s", self.url)

        # Initialize Confluence client
        if username and api_token:
            self.confluence = Confluence(url=self.url, username=username, password=api_token, cloud=True)
        else:
            self.confluence = Confluence(url=self.url, cloud=True)

        logger.info("ConfluenceFileSource initialized for %s", self.url)

    def _extract_base_url(self, page_url: str) -> str:
        """Extract base URL from page URL (scheme://domain/first-path-segment)."""
        parsed = urlparse(page_url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # Include first path segment if it exists (e.g., /confluence, /wiki)
        if path_parts:
            return f"{parsed.scheme}://{parsed.netloc}/{path_parts[0]}"
        return f"{parsed.scheme}://{parsed.netloc}"

    def _parse_page_id(self, page_url: str) -> str:
        """Extract page ID from Confluence URL."""
        parsed = urlparse(page_url)

        # Try query param: ?pageId=123456
        if "pageId" in parsed.query:
            return parse_qs(parsed.query)["pageId"][0]

        # Try path: /pages/123456/... or /spaces/SPACE/pages/123456/...
        match = re.search(r"/pages/(\d+)", parsed.path)
        if match:
            return match.group(1)

        raise ValueError(
            f"Could not extract page ID from URL: {page_url}. "
            "Expected format: /pages/123456 or ?pageId=123456"
        )

    def list_files(self) -> Iterator[FileMetadata]:
        """List pages from Confluence by URL."""
        logger.info("Listing %d page(s) from Confluence", len(self.page_urls))

        for page_url in self.page_urls:
            try:
                page_id = self._parse_page_id(page_url)
                # Get page title for better metadata
                page_info = self.confluence.get_page_by_id(page_id, expand="")
                title = page_info.get("title", page_id)

                yield FileMetadata(
                    path=page_id,
                    name=title,
                    mime_type=None,
                    description=f"Confluence page: {title}",
                )
            except Exception as e:
                logger.warning("Failed to process page URL %s: %s", page_url, e)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Export page content from Confluence."""
        page_id = str(file_metadata.path)
        logger.debug("Exporting Confluence page ID %s as %s", page_id, self.export_format)

        if self.export_format == "pdf":
            return self.confluence.export_page(page_id)

        # For HTML/markdown, get the page body
        expand_map = {"html": "body.view", "markdown": "body.storage"}
        expand = expand_map.get(self.export_format)

        if not expand:
            raise ValueError(f"Unsupported export format: {self.export_format}")

        page = self.confluence.get_page_by_id(page_id, expand=expand)
        body_type = "view" if self.export_format == "html" else "storage"
        content = page.get("body", {}).get(body_type, {}).get("value", "")

        return content.encode("utf-8")

    def get_file_count_estimate(self) -> int | None:
        """Get estimate of page count."""
        return len(self.page_urls)
