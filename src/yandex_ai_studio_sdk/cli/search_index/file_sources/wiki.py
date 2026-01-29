from __future__ import annotations

import logging
from collections.abc import Iterator
from urllib.parse import urlparse

import mwclient  # type: ignore[import-untyped]

from .base import BaseFileSource, FileMetadata

logger = logging.getLogger(__name__)


class WikiFileSource(BaseFileSource):
    """Source for loading page content from MediaWiki instances."""

    def __init__(
        self,
        page_urls: list[str],
        *,
        username: str | None = None,
        password: str | None = None,
        export_format: str = "text",
    ):
        if not page_urls:
            raise ValueError("At least one page URL must be provided")

        self.page_urls = page_urls
        self.export_format = export_format

        # Extract site domain from first page URL
        parsed = urlparse(page_urls[0])
        self.site = mwclient.Site(parsed.netloc, path=parsed.path.split("/wiki/")[0] + "/")

        if username and password:
            self.site.login(username, password)
            logger.debug("Logged in to wiki as %s", username)

        logger.info("WikiFileSource initialized for %s", parsed.netloc)

    def _parse_page_url(self, page_url: str) -> str:
        """
        Parse MediaWiki page URL and extract page title.

        Examples:
        - https://en.wikipedia.org/wiki/Machine_learning -> Machine_learning
        - https://en.wikipedia.org/wiki/Python_(programming_language) -> Python_(programming_language)
        """
        parsed = urlparse(page_url)
        path = parsed.path

        if "/wiki/" in path:
            title = path.split("/wiki/", 1)[1]
            return title

        raise ValueError(f"Unable to parse MediaWiki page URL: {page_url}")

    def list_files(self) -> Iterator[FileMetadata]:
        """List pages from MediaWiki by URL."""
        logger.info("Listing %d page(s) from wiki", len(self.page_urls))

        for page_url in self.page_urls:
            try:
                page_title = self._parse_page_url(page_url)
                yield FileMetadata(
                    path=page_title,
                    name=page_title.replace("_", " "),
                    mime_type=None,
                    description=f"Wiki page: {page_title.replace('_', ' ')}",
                )
            except Exception as e:
                logger.warning("Failed to process page URL %s: %s", page_url, e)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Get page content using mwclient."""
        page_title = str(file_metadata.path)
        logger.debug("Getting content for page: %s", page_title)

        page = self.site.pages[page_title]

        if not page.exists:
            raise ValueError(f"Page not found: {page_title}")

        if self.export_format == "html":
            # Get HTML rendering of the page
            html_content = page.html()
            return html_content.encode("utf-8")
        else:
            # Get plain text extract using TextExtracts API
            result = self.site.api(
                "query",
                titles=page_title,
                prop="extracts",
                explaintext=True,
            )
            pages = result.get("query", {}).get("pages", {})
            page_data = next(iter(pages.values()))

            if "extract" not in page_data:
                raise ValueError(f"No content available for page: {page_title}")

            text_content = page_data["extract"]
            return text_content.encode("utf-8")

    def get_file_count_estimate(self) -> int | None:
        """Get estimate of page count."""
        count = len(self.page_urls)
        logger.info("Estimated %d page(s)", count)
        return count
