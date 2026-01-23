from __future__ import annotations

import click

from ..file_sources.base import BaseFileSource
from ..utils import all_common_options, create_command_executor
from .base import BaseCommand


# Placeholder - WikiFileSource not yet implemented
class WikiFileSource(BaseFileSource):
    """Placeholder for Wiki file source (not yet implemented)."""

    def __init__(self, **kwargs):
        raise NotImplementedError("WikiFileSource is not yet implemented")

    def list_files(self):
        raise NotImplementedError("WikiFileSource is not yet implemented")

    def get_file_content(self, file_metadata):
        raise NotImplementedError("WikiFileSource is not yet implemented")

    def get_file_count_estimate(self):
        return None


class WikiCommand(BaseCommand):
    """Command for creating search index from MediaWiki."""

    def __init__(
        self,
        # Wiki-specific options
        api_url: str,
        username: str | None,
        password: str | None,
        category: str | None,
        namespace: int | None,
        page_titles: tuple[str, ...],
        export_format: str,
        # Common options
        **kwargs,
    ):
        """Initialize Wiki command with Wiki-specific and common parameters."""
        self.api_url = api_url
        self.username = username
        self.password = password
        self.category = category
        self.namespace = namespace
        self.page_titles = page_titles
        self.export_format = export_format

        # Note: Authentication is optional for public wikis like Wikipedia
        # Validation will happen in WikiFileSource if needed

        # Initialize base command
        super().__init__(**kwargs)

    def create_file_source(self) -> BaseFileSource:
        """Create WikiFileSource with configured parameters."""
        return WikiFileSource(
            api_url=self.api_url,
            username=self.username,
            password=self.password,
            category=self.category,
            namespace=self.namespace,
            page_titles=list(self.page_titles) if self.page_titles else None,
            export_format=self.export_format,
        )


@click.command(name="wiki")
@click.option(
    "--api-url",
    required=True,
    help="MediaWiki API URL (e.g., https://en.wikipedia.org/w/api.php)",
)
@click.option(
    "--username",
    envvar="WIKI_USERNAME",
    help="Wiki username (or use WIKI_USERNAME env var)",
)
@click.option(
    "--password",
    envvar="WIKI_PASSWORD",
    help="Wiki password (or use WIKI_PASSWORD env var)",
)
@click.option(
    "--category",
    help="Export all pages from this category",
)
@click.option(
    "--namespace",
    type=int,
    help="MediaWiki namespace to export from",
)
@click.option(
    "--page-title",
    "page_titles",
    multiple=True,
    help="Specific page titles to export (can be specified multiple times)",
)
@click.option(
    "--export-format",
    type=click.Choice(["pdf", "html", "markdown"]),
    default="pdf",
    show_default=True,
    help="Format for exporting pages",
)
@all_common_options
def wiki_command(**kwargs):
    """
    Create a search index from MediaWiki.

    This command exports pages from a MediaWiki instance (like Wikipedia),
    uploads them to Yandex Cloud, and creates a search index.

    Authentication is optional and only needed for private wikis.
    """
    create_command_executor(WikiCommand, **kwargs)
