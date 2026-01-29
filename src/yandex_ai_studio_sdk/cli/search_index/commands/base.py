from __future__ import annotations

import abc
import asyncio
import json
import logging
import sys

import click
from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._types.misc import UNDEFINED
from yandex_ai_studio_sdk.cli.search_index.constants import LOG_DATE_FORMAT, LOG_FORMAT
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource
from yandex_ai_studio_sdk.cli.search_index.legacy_mapper import LegacyYandexMapper
from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams, OpenAIVectorStoreCreateParams
from yandex_ai_studio_sdk.cli.search_index.uploader import AsyncSearchIndexUploader, UploadConfig
from yandex_ai_studio_sdk.search_indexes import (
    HybridSearchIndexType, StaticIndexChunkingStrategy, TextSearchIndexType, VectorSearchIndexType
)

logger = logging.getLogger(__name__)


class BaseCommand(abc.ABC):
    """
    Base class for all CLI commands.
    """

    def __init__(
        self,
        # SDK options
        folder_id: str | None,
        auth: str | None,
        endpoint: str | None,
        verbose: int,
        # Vector store options (OpenAI-compatible)
        name: str | None,
        metadata: tuple[str, ...],
        expires_after_days: int | None,
        expires_after_anchor: str | None,
        max_chunk_size_tokens: int,
        chunk_overlap_tokens: int,
        # File options (OpenAI-compatible)
        file_purpose: str,
        file_expires_after_seconds: int | None,
        file_expires_after_anchor: str | None,
        max_concurrent_uploads: int,
        skip_on_error: bool,
        # Output options
        output_format: str,
    ):
        """Initialize base command with OpenAI-compatible parameters."""
        # SDK options
        self.folder_id = folder_id
        self.auth = auth
        self.endpoint = endpoint
        self.verbose = verbose

        self.openai_file_create_params = OpenAIFileCreateParams(
            name=None,
            purpose=file_purpose,
            expires_after_seconds=file_expires_after_seconds,
            expires_after_anchor=file_expires_after_anchor,  # type: ignore[arg-type]
        )

        self.openai_vector_store_create_params = OpenAIVectorStoreCreateParams(
            name=name,
            metadata=self.parse_labels(metadata) if metadata else None,
            expires_after_days=expires_after_days,
            expires_after_anchor=expires_after_anchor,  # type: ignore[arg-type]
            chunking_strategy=self.create_search_index_type(
                max_chunk_size_tokens,
                chunk_overlap_tokens
            ),
        )

        self.max_concurrent_uploads = max_concurrent_uploads
        self.skip_on_error = skip_on_error
        self.output_format = output_format

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

    def create_sdk(self) -> AsyncAIStudio:
        """Create and configure AsyncAIStudio SDK instance."""
        try:
            sdk = AsyncAIStudio(
                folder_id=self.folder_id if self.folder_id else UNDEFINED,
                auth=self.auth if self.auth else UNDEFINED,
                endpoint=self.endpoint if self.endpoint else UNDEFINED,
            )
            logger.info("SDK initialized successfully")
            return sdk
        except Exception as e:
            self._output_error(f"Error initializing SDK: {e}")
            sys.exit(1)

    @staticmethod
    def parse_labels(label_tuples: tuple[str, ...]) -> dict[str, str]:
        """Parse label strings in format 'KEY=VALUE' into a dictionary."""
        labels = {}
        for label_str in label_tuples:
            if "=" not in label_str:
                logger.warning("Invalid label format '%s', expected KEY=VALUE", label_str)
                continue
            key, value = label_str.split("=", 1)
            labels[key.strip()] = value.strip()
        return labels

    def create_search_index_type(
        self,
        max_chunk_size_tokens: int,
        chunk_overlap_tokens: int,
    ) -> HybridSearchIndexType:
        """
        Create search index type configuration.

        For OpenAI compatibility, we always use hybrid index (vector store).
        """
        chunking_strategy = StaticIndexChunkingStrategy(
            max_chunk_size_tokens=max_chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
        )

        return HybridSearchIndexType(
            text_search_index=TextSearchIndexType(
                chunking_strategy=chunking_strategy
            ),
            vector_search_index=VectorSearchIndexType(
                chunking_strategy=chunking_strategy
            ),
        )

    def create_upload_config(self) -> UploadConfig:
        """
        Create upload configuration from OpenAI-compatible CLI parameters.

        TODO: Remove this method when migrating to native OpenAI API.
        Uses LegacyYandexMapper to convert OpenAI params to Yandex SDK format.
        """
        return LegacyYandexMapper.create_legacy_upload_config(
            file_create_params=self.openai_file_create_params,
            vector_store_create_params=self.openai_vector_store_create_params,
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

    def execute(self) -> None:
        """Execute the command: create file source, upload files, create index."""
        try:
            asyncio.run(self._execute_async())
        except Exception as e:
            self._output_error(f"Error during upload: {e}")
            logger.exception("Upload failed")
            sys.exit(1)

    async def _execute_async(self) -> None:
        """Async implementation of execute."""
        file_source = self.create_file_source()
        config = self.create_upload_config()

        uploader = AsyncSearchIndexUploader(self.sdk, config)
        search_index = await uploader.upload_from_source(file_source)

        self._output_success(search_index)

    def _output_success(self, search_index) -> None:
        """Output success message with search index details."""
        if self.output_format == "json":
            result = {
                "status": "success",
                "folder_id": self.folder_id,
                "search_index": {
                    "id": search_index.id,
                    "name": search_index.name,
                },
            }
            print(json.dumps(result))
        else:
            click.echo("\nSearch index created successfully!")
            click.echo(f"Search Index ID: {search_index.id}")
            if search_index.name:
                click.echo(f"Name: {search_index.name}")
            if self.folder_id:
                click.echo(f"Folder ID: {self.folder_id}")

    def _output_error(self, message: str) -> None:
        """Output error message in the configured format."""
        if self.output_format == "json":
            result = {
                "status": "error",
                "error": message,
            }
            print(json.dumps(result))
        else:
            click.echo(f"\n{message}", err=True)
