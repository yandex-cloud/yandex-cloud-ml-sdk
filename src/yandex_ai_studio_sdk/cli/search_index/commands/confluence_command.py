from __future__ import annotations

import click

from ..file_sources.base import BaseFileSource
from ..file_sources.confluence import ConfluenceFileSource
from ..utils import all_common_options, create_command_executor, validate_authentication
from .base import BaseCommand


class ConfluenceCommand(BaseCommand):
    """Command for creating search index from Atlassian Confluence pages."""

    def __init__(
        self,
        # Confluence-specific options
        page_urls: tuple[str, ...],
        base_url: str | None,
        username: str | None,
        api_token: str | None,
        export_format: str,
        # Common options
        **kwargs,
    ):
        """Initialize Confluence command with Confluence-specific and common parameters."""
        self.page_urls = page_urls
        self.base_url = base_url
        self.username = username
        self.api_token = api_token
        self.export_format = export_format

        # Validate authentication (optional for public instances)
        if self.username or self.api_token:
            # If either is provided, both must be provided
            self.username, self.api_token = validate_authentication(
                self.username,
                self.api_token,
                auth_type="Confluence authentication",
            )

        # Initialize base command
        super().__init__(**kwargs)

    def create_file_source(self) -> BaseFileSource:
        """Create ConfluenceFileSource with configured parameters."""
        return ConfluenceFileSource(
            page_urls=list(self.page_urls),
            base_url=self.base_url,
            username=self.username,
            api_token=self.api_token,
            export_format=self.export_format,
        )


@click.command(name="confluence")
@click.option(
    "--page-url",
    "page_urls",
    multiple=True,
    required=True,
    help="Page URL(s) to export (e.g., https://your-domain/display/SPACE/Page+Title). Can be specified multiple times.",
)
@click.option(
    "--base-url",
    help="Confluence base URL (e.g., https://cwiki.apache.org/confluence). If not specified, extracted from first page URL.",
)
@click.option(
    "--username",
    envvar="CONFLUENCE_USERNAME",
    help="Confluence username (email) - optional for public instances (or use CONFLUENCE_USERNAME env var)",
)
@click.option(
    "--api-token",
    envvar="CONFLUENCE_API_TOKEN",
    help="Confluence API token - optional for public instances (or use CONFLUENCE_API_TOKEN env var)",
)
@click.option(
    "--export-format",
    type=click.Choice(["pdf", "html", "markdown"]),
    default="pdf",
    show_default=True,
    help="Format for exporting pages",
)
@all_common_options
def confluence_command(**kwargs):
    """
    Create a search index from Atlassian Confluence pages.

    This command exports page content from Confluence by URL,
    uploads it to Yandex Cloud, and creates a search index.

    Simply copy the page URL from your browser and use it with --page-url.
    You can specify multiple pages by using --page-url multiple times.

    Authentication is optional. For public Confluence instances, you can omit
    --username and --api-token. For private instances, provide credentials via
    command line options or CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN environment variables.
    """
    create_command_executor(ConfluenceCommand, **kwargs)
