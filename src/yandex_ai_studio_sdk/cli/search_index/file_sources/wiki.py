from __future__ import annotations

import logging
from collections.abc import Iterator
from urllib.parse import urlparse

import requests

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

        # Extract API URL from first page URL
        self.api_url = self._extract_api_url(page_urls[0])
        self.page_urls = page_urls
        self.username = username
        self.password = password
        self.export_format = export_format

        self.session = requests.Session()

        if username and password:
            self._login()

        logger.info("WikiFileSource initialized for %s", self.api_url)

    def _login(self) -> None:
        """Login to MediaWiki using username and password."""
        response = self.session.get(
            self.api_url,
            params={"action": "query", "meta": "tokens", "type": "login", "format": "json"}
        )
        response.raise_for_status()
        login_token = response.json()["query"]["tokens"]["logintoken"]

        response = self.session.post(
            self.api_url,
            data={
                "action": "login",
                "lgname": self.username,
                "lgpassword": self.password,
                "lgtoken": login_token,
                "format": "json",
            }
        )
        response.raise_for_status()
        result = response.json()

        if result.get("login", {}).get("result") != "Success":
            raise ValueError(f"Wiki login failed: {result}")

        logger.debug("Logged in to wiki as %s", self.username)

    def _extract_api_url(self, page_url: str) -> str:
        """Extract MediaWiki API URL from page URL."""
        parsed = urlparse(page_url)
        return f"{parsed.scheme}://{parsed.netloc}/w/api.php"

    def _parse_page_url(self, page_url: str) -> str:
        """
        Parse MediaWiki page URL and extract page title.

        Examples:
        - https://en.wikipedia.org/wiki/Machine_learning -> Machine learning
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
                    name=page_title,
                    mime_type=None,
                    description=f"Wiki page: {page_title}",
                )
            except Exception as e:
                logger.warning("Failed to process page URL %s: %s", page_url, e)

    def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Get page content."""
        page_title = str(file_metadata.path)
        logger.debug("Getting content for page: %s", page_title)

        if self.export_format == "html":
            params = {
                "action": "parse",
                "page": page_title,
                "prop": "text",
                "format": "json",
            }
            response = self.session.get(self.api_url, params=params)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            if "parse" not in data or "text" not in data["parse"]:
                raise ValueError(f"Failed to parse page: {page_title}")

            html_content = data["parse"]["text"]["*"]
            return html_content.encode("utf-8")

        else:  # text or markdown - both get plain text
            params = {
                "action": "query",
                "titles": page_title,
                "prop": "extracts",
                "explaintext": "true",
                "format": "json",
            }
            response = self.session.get(self.api_url, params=params)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            if "query" not in data or "pages" not in data["query"]:
                raise ValueError(f"Failed to get page content for: {page_title}")

            page = next(iter(data["query"]["pages"].values()))
            if "missing" in page or "extract" not in page:
                raise ValueError(f"Page not found or no content: {page_title}")

            text_content = page["extract"]
            return text_content.encode("utf-8")

    def get_file_count_estimate(self) -> int | None:
        """Get estimate of page count."""
        count = len(self.page_urls)
        logger.info("Estimated %d page(s)", count)
        return count
