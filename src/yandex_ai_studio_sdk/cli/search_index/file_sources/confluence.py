from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from urllib.parse import parse_qs, urlparse

from atlassian import Confluence  # type: ignore[import-untyped]

from .base import BaseFileSource, FileMetadata

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

        self.url = self._resolve_base_url(page_urls, base_url)
        self.page_urls = page_urls
        self.username = username
        self.api_token = api_token
        self.export_format = export_format

        if self.username and self.api_token:
            self.confluence = Confluence(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True,
            )
        else:
            self.confluence = Confluence(url=self.url, cloud=True)

        logger.info("ConfluenceFileSource initialized for %s", self.url)

    def list_files(self) -> Iterator[FileMetadata]:
        """List pages from Confluence by URL."""
        logger.info("Listing %d page(s) from Confluence", len(self.page_urls))

        for page_url in self.page_urls:
            try:
                page_id = self._parse_page_url(page_url)
                yield FileMetadata(
                    path=page_id,
                    name=page_url,  # Use URL as name for simplicity
                    mime_type=None,
                    description=f"Confluence page: {page_url}",
                )
            except Exception as e:
                logger.warning("Failed to process page URL %s: %s", page_url, e)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Export page content from Confluence."""
        page_id = str(file_metadata.path)
        logger.debug("Getting content for Confluence page ID: %s", page_id)
        return self._export_page(page_id, self.export_format)

    def get_file_count_estimate(self) -> int | None:
        """Get estimate of page count."""
        count = len(self.page_urls)
        logger.info("Estimated %d page(s)", count)
        return count

    def _export_page(self, page_id: str, export_format: str) -> bytes:
        """Export a page in the specified format."""
        if export_format == "pdf":
            return self.confluence.export_page(page_id)

        # Map format to Confluence body type
        body_types = {"html": "view", "markdown": "storage"}
        body_type = body_types.get(export_format)

        if body_type:
            page = self.confluence.get_page_by_id(page_id, expand=f"body.{body_type}")
            return page.get("body", {}).get(body_type, {}).get("value", "").encode("utf-8")

        raise ValueError(f"Unsupported export format: {export_format}")

    def _resolve_base_url(self, page_urls: list[str], base_url: str | None) -> str:
        """Resolve base URL: validate if provided, or extract from first page URL."""
        if base_url:
            # Validate that all page URLs start with provided base URL
            normalized_base = base_url.rstrip('/')
            for page_url in page_urls:
                if not page_url.startswith(normalized_base):
                    raise ValueError(
                        f"Page URL {page_url} does not start with base URL {normalized_base}"
                    )
            return normalized_base

        # Extract base URL from first page URL
        extracted = self._extract_base_url(page_urls[0])
        logger.info("Extracted base URL: %s", extracted)
        return extracted

    def _extract_base_url(self, page_url: str) -> str:
        """Extract base URL from page URL (scheme + netloc + first path segment)."""
        parsed = urlparse(page_url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # Use first path segment if present (e.g., /confluence or /wiki)
        if path_parts:
            return f"{parsed.scheme}://{parsed.netloc}/{path_parts[0]}"

        return f"{parsed.scheme}://{parsed.netloc}"

    def _parse_page_url(self, page_url: str) -> str:
        """Parse Confluence page URL and extract page ID."""
        parsed = urlparse(page_url)

        # Format 1: ?pageId=123456
        if "pageId" in parsed.query:
            return parse_qs(parsed.query)["pageId"][0]

        # Format 2: /pages/123456/... or /spaces/SPACE/pages/123456/...
        match = re.search(r"/pages/(\d+)", parsed.path)
        if match:
            return match.group(1)

        raise ValueError(
            f"Could not extract page ID from URL: {page_url}. "
            "URL must contain page ID in format /pages/123456 or ?pageId=123456"
        )
