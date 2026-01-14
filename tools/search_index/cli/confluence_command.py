from __future__ import annotations

from typing import Optional

import click

from tools.search_index.cli.base import BaseCommand
from tools.search_index.cli.utils import all_common_options, create_command_executor, validate_authentication
from tools.search_index.file_sources import ConfluenceFileSource
from tools.search_index.file_sources.base import BaseFileSource


class ConfluenceCommand(BaseCommand):
    """Command for creating search index from Atlassian Confluence."""

    def __init__(
        self,
        # Confluence-specific options
        url: str,
        username: str | None,
        api_token: str | None,
        space_key: str | None,
        page_ids: tuple[str, ...],
        include_attachments: bool,
        export_format: str,
        # Common options
        **kwargs,
    ):
        """Initialize Confluence command with Confluence-specific and common parameters."""
        self.url = url
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.page_ids = page_ids
        self.include_attachments = include_attachments
        self.export_format = export_format

        # Validate authentication
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
            url=self.url,
            username=self.username,
            api_token=self.api_token,
            space_key=self.space_key,
            page_ids=list(self.page_ids) if self.page_ids else None,
            include_attachments=self.include_attachments,
            export_format=self.export_format,
        )


@click.command(name="confluence")
@click.option(
    "--url",
    required=True,
    help="Confluence instance URL (e.g., https://your-domain.atlassian.net/wiki)",
)
@click.option(
    "--username",
    envvar="CONFLUENCE_USERNAME",
    help="Confluence username (email) (or use CONFLUENCE_USERNAME env var)",
)
@click.option(
    "--api-token",
    envvar="CONFLUENCE_API_TOKEN",
    help="Confluence API token (or use CONFLUENCE_API_TOKEN env var)",
)
@click.option(
    "--space-key",
    help="Confluence space key to export",
)
@click.option(
    "--page-id",
    "page_ids",
    multiple=True,
    help="Specific page IDs to export (can be specified multiple times)",
)
@click.option(
    "--include-attachments/--no-include-attachments",
    default=True,
    show_default=True,
    help="Whether to include page attachments",
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
    Create a search index from Atlassian Confluence.

    This command exports pages and attachments from Confluence,
    uploads them to Yandex Cloud, and creates a search index.

    Authentication is required via --username and --api-token options
    or CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN environment variables.
    """
    create_command_executor(ConfluenceCommand, **kwargs)
