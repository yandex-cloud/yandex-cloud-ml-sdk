from __future__ import annotations

import abc
import asyncio
import logging
import sys
from typing import Optional

import click

from tools.search_index.constants import LOG_DATE_FORMAT, LOG_FORMAT
from tools.search_index.file_sources.base import BaseFileSource
from tools.search_index.uploader import AsyncSearchIndexUploader, UploadConfig
from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk.search_indexes import (
    HybridSearchIndexType, StaticIndexChunkingStrategy, TextSearchIndexType, VectorSearchIndexType
)

logger = logging.getLogger(__name__)


class BaseCommand(abc.ABC):
    """
    Base class for all CLI commands.

    This class provides common functionality for:
    - SDK initialization
    - Upload configuration creation
    - File source creation (abstract)
    - Upload execution
    - Error handling
    """

    def __init__(
        self,
        # SDK options
        folder_id: str | None,
        auth: str | None,
        endpoint: str | None,
        verbose: int,
        # Index options
        index_name: str | None,
        index_description: str | None,
        index_labels: tuple[str, ...],
        index_ttl_days: int | None,
        index_expiration_policy: str | None,
        index_type: str,
        max_chunk_size_tokens: int,
        chunk_overlap_tokens: int,
        # File options
        file_ttl_days: int | None,
        file_expiration_policy: str | None,
        file_labels: tuple[str, ...],
        delete_files: bool,
        batch_size: int,
        max_concurrent_uploads: int,
        skip_on_error: bool,
    ):
        """Initialize base command with common parameters."""
        # SDK options
        self.folder_id = folder_id
        self.auth = auth
        self.endpoint = endpoint
        self.verbose = verbose

        # Index options
        self.index_name = index_name
        self.index_description = index_description
        self.index_labels = index_labels
        self.index_ttl_days = index_ttl_days
        self.index_expiration_policy = index_expiration_policy
        self.index_type = index_type
        self.max_chunk_size_tokens = max_chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

        # File options
        self.file_ttl_days = file_ttl_days
        self.file_expiration_policy = file_expiration_policy
        self.file_labels = file_labels
        self.delete_files = delete_files
        self.batch_size = batch_size
        self.max_concurrent_uploads = max_concurrent_uploads
        self.skip_on_error = skip_on_error

        # Initialize SDK
        self.setup_logging()
        self.sdk = self.create_sdk()

    def setup_logging(self) -> None:
        """Configure logging based on verbosity level."""
        if self.verbose == 0:
            level = logging.WARNING
        elif self.verbose == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG

        logging.basicConfig(
            level=level,
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
        )

    def create_sdk(self) -> AsyncYCloudML:
        """Create and configure AsyncYCloudML SDK instance."""
        try:
            kwargs = {}
            if self.folder_id:
                kwargs["folder_id"] = self.folder_id
            if self.auth:
                kwargs["auth"] = self.auth
            if self.endpoint:
                kwargs["endpoint"] = self.endpoint

            sdk = AsyncYCloudML(**kwargs)
            logger.info("SDK initialized successfully")
            return sdk
        except Exception as e:
            click.echo(f"Error initializing SDK: {e}", err=True)
            sys.exit(1)

    @staticmethod
    def parse_labels(label_tuples: tuple[str, ...]) -> dict[str, str]:
        """Parse label strings in format 'KEY=VALUE' into a dictionary."""
        labels = {}
        for label_str in label_tuples:
            if "=" not in label_str:
                click.echo(f"Warning: Invalid label format '{label_str}', expected KEY=VALUE", err=True)
                continue
            key, value = label_str.split("=", 1)
            labels[key.strip()] = value.strip()
        return labels

    def create_search_index_type(
        self,
    ) -> TextSearchIndexType | VectorSearchIndexType | HybridSearchIndexType | None:
        """Create search index type configuration."""
        if self.index_type == "text":
            return TextSearchIndexType(
                chunking_strategy=StaticIndexChunkingStrategy(
                    max_chunk_size_tokens=self.max_chunk_size_tokens,
                    chunk_overlap_tokens=self.chunk_overlap_tokens,
                )
            )
        elif self.index_type == "vector":
            return VectorSearchIndexType(
                chunking_strategy=StaticIndexChunkingStrategy(
                    max_chunk_size_tokens=self.max_chunk_size_tokens,
                    chunk_overlap_tokens=self.chunk_overlap_tokens,
                )
            )
        elif self.index_type == "hybrid":
            return HybridSearchIndexType(
                text_search_index=TextSearchIndexType(
                    chunking_strategy=StaticIndexChunkingStrategy(
                        max_chunk_size_tokens=self.max_chunk_size_tokens,
                        chunk_overlap_tokens=self.chunk_overlap_tokens,
                    )
                ),
                vector_search_index=VectorSearchIndexType(
                    chunking_strategy=StaticIndexChunkingStrategy(
                        max_chunk_size_tokens=self.max_chunk_size_tokens,
                        chunk_overlap_tokens=self.chunk_overlap_tokens,
                    )
                ),
            )
        return None

    def create_upload_config(self) -> UploadConfig:
        """Create upload configuration from CLI parameters."""
        return UploadConfig(
            # File settings
            file_ttl_days=self.file_ttl_days,
            file_expiration_policy=self.file_expiration_policy,
            file_labels=self.parse_labels(self.file_labels) if self.file_labels else None,
            # Index settings
            index_name=self.index_name,
            index_description=self.index_description,
            index_labels=self.parse_labels(self.index_labels) if self.index_labels else None,
            index_ttl_days=self.index_ttl_days,
            index_expiration_policy=self.index_expiration_policy,
            index_type=self.create_search_index_type(),
            # Upload behavior
            batch_size=self.batch_size,
            delete_files_after_indexing=self.delete_files,
            skip_on_error=self.skip_on_error,
            max_concurrent_uploads=self.max_concurrent_uploads,
        )

    @abc.abstractmethod
    def create_file_source(self) -> BaseFileSource:
        """
        Create file source specific to this command.

        This method must be implemented by subclasses to return
        the appropriate file source (LocalFileSource, S3FileSource, etc.)
        """
        pass

    def execute(self) -> None:
        """Execute the command: create file source, upload files, create index."""
        try:
            asyncio.run(self._execute_async())
        except KeyboardInterrupt:
            click.echo("\n\nUpload interrupted by user.", err=True)
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            click.echo(f"\nError during upload: {e}", err=True)
            logger.exception("Upload failed")
            sys.exit(1)

    async def _execute_async(self) -> None:
        """Async implementation of execute."""
        # Create file source
        file_source = self.create_file_source()

        # Create upload configuration
        config = self.create_upload_config()

        # Execute upload
        uploader = AsyncSearchIndexUploader(self.sdk, config)
        search_index = await uploader.upload_from_source(file_source)

        # Output results
        self.output_success(search_index)

    def output_success(self, search_index) -> None:
        """Output success message with search index details."""
        click.echo("\nSearch index created successfully!")
        click.echo(f"Search Index ID: {search_index.id}")

        if search_index.name:
            click.echo(f"Name: {search_index.name}")
