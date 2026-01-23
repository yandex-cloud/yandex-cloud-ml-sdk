from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import cast

from tqdm.asyncio import tqdm

from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._files.file import File
from yandex_cloud_ml_sdk._search_indexes.index_type import BaseSearchIndexType
from yandex_cloud_ml_sdk._search_indexes.search_index import AsyncSearchIndex
from yandex_cloud_ml_sdk._types.misc import UNDEFINED

from .constants import BYTES_PER_MB, DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS, DEFAULT_SKIP_ON_ERROR
from .file_sources.base import BaseFileSource, FileMetadata

logger = logging.getLogger(__name__)


@dataclass
class UploadConfig:
    """Configuration for file upload and search index creation."""

    # File upload settings
    file_ttl_days: int | None = None
    """Time-to-live for uploaded files in days"""

    file_expiration_policy: str | None = None
    """Expiration policy for files ('static' or 'since_last_active')"""

    file_labels: dict[str, str] | None = None
    """Labels to attach to all uploaded files"""

    # Search index settings
    index_name: str | None = None
    """Name for the search index"""

    index_description: str | None = None
    """Description for the search index"""

    index_labels: dict[str, str] | None = None
    """Labels to attach to the search index"""

    index_ttl_days: int | None = None
    """Time-to-live for the search index in days"""

    index_expiration_policy: str | None = None
    """Expiration policy for the index ('static' or 'since_last_active')"""

    index_type: BaseSearchIndexType | None = None
    """Type of search index to create (text, vector, or hybrid)"""

    # Upload behavior settings
    batch_size: int = DEFAULT_BATCH_SIZE
    """Number of files to upload before adding them to the index (currently unused)"""

    delete_files_after_indexing: bool = False
    """Whether to delete uploaded files after adding them to the index"""

    skip_on_error: bool = DEFAULT_SKIP_ON_ERROR
    """Whether to skip files that fail to upload instead of stopping"""

    max_concurrent_uploads: int = DEFAULT_MAX_WORKERS
    """Maximum number of concurrent upload tasks"""

    show_progress: bool = True
    """Whether to show progress bar during upload"""


@dataclass
class UploadStats:
    """Statistics about the upload process."""

    total_files: int = 0
    """Total number of files processed"""

    uploaded_files: int = 0
    """Number of files successfully uploaded"""

    failed_files: int = 0
    """Number of files that failed to upload"""

    skipped_files: int = 0
    """Number of files skipped"""

    total_bytes: int = 0
    """Total bytes uploaded"""


class AsyncSearchIndexUploader:
    """Asynchronous uploader for creating search indexes from various file sources."""

    def __init__(
        self,
        sdk: AsyncYCloudML,
        config: UploadConfig | None = None,
    ):
        """
        Initialize the search index uploader.

        Args:
            sdk: Initialized AsyncYCloudML SDK instance
            config: Upload configuration (uses defaults if not provided)
        """
        self.sdk = sdk
        self.config = config or UploadConfig()
        self.stats = UploadStats()
        self._uploaded_files: list[File] = []

    async def upload_from_source(
        self,
        source: BaseFileSource,
    ) -> AsyncSearchIndex:
        """
        Upload files from a source and create a search index.

        Args:
            source: File source to upload from
        """
        logger.info("Starting upload from source: %s", source.__class__.__name__)


        # Upload files
        uploaded_files = await self._upload_files(source)
        if not uploaded_files:
            raise ValueError("No files were uploaded successfully")
        logger.info("Uploaded %d files, creating search index...", len(uploaded_files))

        # Create search index
        search_index = await self._create_search_index(uploaded_files)

        # Cleanup (if requested)
        if self.config.delete_files_after_indexing:
            await self._cleanup_files(uploaded_files)

        logger.info("Search index created successfully: %s", search_index.id)
        self._log_stats()
        return search_index


    async def _upload_files(self, source: BaseFileSource) -> list[File]:
        """
        Upload all files from the source with concurrent execution.

        Args:
            source: File source to upload from
        """
        # Get file count estimate for progress tracking
        file_count = source.get_file_count_estimate()
        if file_count:
            logger.info("Estimated files to process: %d", file_count)

        # Collect all files and their content
        files_to_upload: list[tuple[FileMetadata, bytes]] = []

        for file_metadata in source.list_files():
            self.stats.total_files += 1

            # Read file content
            try:
                content = source.get_file_content(file_metadata)
                self.stats.total_bytes += len(content)
                files_to_upload.append((file_metadata, content))
            except Exception as e:
                logger.error("Failed to read file %s: %s", file_metadata.path, e)
                self.stats.failed_files += 1
                if not self.config.skip_on_error:
                    raise
                continue

        if not files_to_upload:
            logger.warning("No files to upload")
            return []

        # Create semaphore to limit concurrent uploads
        semaphore = asyncio.Semaphore(self.config.max_concurrent_uploads)

        # Upload files concurrently with progress bar
        tasks = [
            self._upload_single_file_with_semaphore(file_metadata, content, semaphore)
            for file_metadata, content in files_to_upload
        ]

        results_to_process: list[File | BaseException | None]
        if self.config.show_progress:
            results_raw = await tqdm.gather(
                *tasks,
                desc="Uploading files",
                total=len(tasks),
                unit="file",
            )
            results_to_process = list(results_raw)  # type: ignore[assignment]
        else:
            results_to_process = list(await asyncio.gather(*tasks, return_exceptions=True))

        # Process results
        uploaded_files: list[File] = []
        for i, result in enumerate(results_to_process):
            file_metadata, _ = files_to_upload[i]

            if isinstance(result, BaseException):
                logger.error("Upload failed for %s: %s", file_metadata.path, result)
                self.stats.failed_files += 1
                if not self.config.skip_on_error:
                    raise result
            elif result is not None:
                # result is File here
                assert isinstance(result, File)
                uploaded_files.append(result)
                self._uploaded_files.append(result)
                self.stats.uploaded_files += 1
                logger.debug(
                    "Uploaded file %s (%d/%d)",
                    file_metadata.name,
                    self.stats.uploaded_files,
                    len(files_to_upload),
                )
            else:
                self.stats.failed_files += 1

        logger.info("Upload completed: %d succeeded, %d failed", self.stats.uploaded_files, self.stats.failed_files)
        return uploaded_files

    async def _upload_single_file_with_semaphore(
        self,
        file_metadata: FileMetadata,
        content: bytes,
        semaphore: asyncio.Semaphore,
    ) -> File | None:
        """
        Upload a single file with semaphore control for concurrency limiting.

        Args:
            file_metadata: Metadata about the file
            content: File content as bytes
            semaphore: Semaphore to limit concurrent uploads
        """
        async with semaphore:
            return await self._upload_single_file(file_metadata, content)

    async def _upload_single_file(self, file_metadata: FileMetadata, content: bytes) -> File | None:
        """
        Upload a single file to Yandex Cloud.

        Args:
            file_metadata: Metadata about the file
            content: File content as bytes
        """
        try:
            # Merge file labels from config and metadata
            labels = {}
            if self.config.file_labels:
                labels.update(self.config.file_labels)
            if file_metadata.labels:
                labels.update(file_metadata.labels)

            # Upload file using SDK
            uploaded_file = await self.sdk.files.upload_bytes(
                content,
                name=file_metadata.name if file_metadata.name else UNDEFINED,
                mime_type=file_metadata.mime_type if file_metadata.mime_type else UNDEFINED,
                ttl_days=self.config.file_ttl_days if self.config.file_ttl_days is not None else UNDEFINED,
                expiration_policy=cast(str, self.config.file_expiration_policy) if self.config.file_expiration_policy else UNDEFINED,  # type: ignore[arg-type]
                labels=labels if labels else UNDEFINED,
            )

            logger.debug("Successfully uploaded file: %s (id: %s)", file_metadata.name, uploaded_file.id)
            return cast(File, uploaded_file)

        except Exception as e:
            logger.error("Failed to upload file %s: %s", file_metadata.name, e)
            if not self.config.skip_on_error:
                raise
            return None

    async def _create_search_index(self, files: list[File]) -> AsyncSearchIndex:
        """
        Create a search index from uploaded files.

        Args:
            files: List of uploaded File objects
        """
        logger.info("Creating search index with %d files...", len(files))

        # Create search index using deferred operation
        operation = await self.sdk.search_indexes.create_deferred(
            files=files,
            index_type=self.config.index_type if self.config.index_type else UNDEFINED,
            name=self.config.index_name if self.config.index_name else UNDEFINED,
            description=self.config.index_description if self.config.index_description else UNDEFINED,
            labels=self.config.index_labels if self.config.index_labels else UNDEFINED,
            ttl_days=self.config.index_ttl_days if self.config.index_ttl_days is not None else UNDEFINED,
            expiration_policy=cast(str, self.config.index_expiration_policy) if self.config.index_expiration_policy else UNDEFINED,  # type: ignore[arg-type]
        )

        logger.info("Search index creation started, waiting for completion...")

        # Wait for operation to complete
        search_index = await operation.wait()

        logger.info("Search index created successfully: %s", search_index.id)
        return search_index

    async def _cleanup_files(self, files: list[File]) -> None:
        """
        Delete uploaded files after they've been added to the index.

        Args:
            files: List of File objects to delete
        """
        if not files:
            return

        logger.info("Cleaning up %d uploaded files...", len(files))

        async def delete_file(file: File) -> bool:
            try:
                file.delete()
                logger.debug("Deleted file: %s", file.id)
                return True
            except Exception as e:
                logger.warning("Failed to delete file %s: %s", file.id, e)
                return False

        results = await asyncio.gather(*[delete_file(file) for file in files], return_exceptions=False)

        deleted_count = sum(1 for r in results if r)
        failed_count = len(results) - deleted_count

        logger.info("Cleanup completed: %d deleted, %d failed", deleted_count, failed_count)

    def _log_stats(self) -> None:
        """Log upload statistics."""
        logger.info("Upload statistics:")
        logger.info("  Total files: %d", self.stats.total_files)
        logger.info("  Uploaded: %d", self.stats.uploaded_files)
        logger.info("  Failed: %d", self.stats.failed_files)
        logger.info("  Skipped: %d", self.stats.skipped_files)
        logger.info(
            "  Total bytes: %d (%.2f MB)",
            self.stats.total_bytes,
            self.stats.total_bytes / BYTES_PER_MB,
        )
