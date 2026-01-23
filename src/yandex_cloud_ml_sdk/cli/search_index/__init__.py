from __future__ import annotations

import click

from .commands.confluence_command import confluence_command
from .commands.local_command import local_command
from .commands.s3_command import s3_command
from .commands.wiki_command import wiki_command


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Create Yandex Cloud search indexes from various file sources.

    This tool helps you upload files from different sources (local filesystem,
    S3, Confluence, Wiki) and create search indexes for use with Yandex Cloud
    Assistants API.
    """


# Register subcommands
cli.add_command(local_command)
cli.add_command(s3_command)
cli.add_command(confluence_command)
cli.add_command(wiki_command)


__all__ = [
    "cli",
    "local_command",
    "s3_command",
    "confluence_command",
    "wiki_command",
]


def main():
    cli()


if __name__ == "__main__":
    main()
