from __future__ import annotations

import click

from ..file_sources.base import BaseFileSource
from ..file_sources.wiki import WikiFileSource
from ..utils import all_common_options, create_command_executor
from .base import BaseCommand


class WikiCommand(BaseCommand):
    """Command for creating search index from MediaWiki pages."""

    def __init__(
        self,
        # Wiki-specific options
        page_urls: tuple[str, ...],
        username: str | None,
        password: str | None,
        export_format: str,
        # Common options
        **kwargs,
    ):
        """Initialize Wiki command with Wiki-specific and common parameters."""
        self.page_urls = page_urls
        self.username = username
        self.password = password
        self.export_format = export_format

        super().__init__(**kwargs)

    def create_file_source(self) -> BaseFileSource:
        """Create WikiFileSource with configured parameters."""
        return WikiFileSource(
            page_urls=list(self.page_urls),
            username=self.username,
            password=self.password,
            export_format=self.export_format,
        )


@click.command(name="wiki")
@click.option(
    "--page-url",
    "page_urls",
    multiple=True,
    required=True,
    help="Page URL(s) to export (e.g., https://en.wikipedia.org/wiki/Python_(programming_language)). Can be specified multiple times.",
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
    "--export-format",
    type=click.Choice(["text", "html", "markdown"]),
    default="text",
    show_default=True,
    help="Format for exporting page content",
)
@all_common_options
def wiki_command(**kwargs):
    """
    Create a search index from MediaWiki pages.

    This command parses page content from a MediaWiki instance (like Wikipedia),
    uploads it to Yandex Cloud, and creates a search index.

    Simply copy the page URL from your browser and use it with --page-url.
    You can specify multiple pages by using --page-url multiple times.

    Authentication is optional for public wikis like Wikipedia.
    """
    create_command_executor(WikiCommand, **kwargs)
