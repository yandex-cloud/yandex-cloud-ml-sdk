"""
Legacy mapper: OpenAI API → Yandex Cloud SDK

TODO: DELETE THIS FILE when migrating to native OpenAI API implementation

This module provides conversion between OpenAI-compatible API parameters
and legacy Yandex Cloud SDK parameters. All conversion logic is isolated
here for easy deletion during migration.
"""
from __future__ import annotations

from typing import Literal

from .openai_types import ExpiresAfterAnchor, OpenAIFileCreateParams, OpenAIVectorStoreCreateParams
from .uploader import UploadConfig


class LegacyYandexMapper:
    """
    Maps OpenAI-compatible parameters to legacy Yandex Cloud SDK parameters.

    ⚠️ TEMPORARY: This mapper will be removed when we migrate to native OpenAI API.
    All conversion logic is isolated here for easy deletion.
    """

    @staticmethod
    def convert_anchor_to_policy(
        anchor: ExpiresAfterAnchor | None
    ) -> Literal["static", "since_last_active"] | None:
        """
        Convert OpenAI expires_after[anchor] to Yandex expiration_policy.

        OpenAI uses:
        - "created_at" - expire based on creation time
        - "last_active_at" - expire based on last activity

        Yandex uses:
        - "static" - expire based on creation time
        - "since_last_active" - expire based on last activity
        """
        if not anchor:
            return None

        mapping: dict[str, Literal["static", "since_last_active"]] = {
            "created_at": "static",
            "last_active_at": "since_last_active",
        }
        return mapping.get(anchor)

    @staticmethod
    def convert_seconds_to_days(seconds: int | None) -> int | None:
        """
        Convert OpenAI expires_after[seconds] to Yandex ttl_days.

        OpenAI uses seconds, Yandex uses days.
        """
        if seconds is None:
            return None
        return seconds // 86400  # 86400 seconds in a day

    @staticmethod
    def convert_metadata_to_labels(
        metadata: dict[str, str] | None
    ) -> dict[str, str] | None:
        """
        Convert OpenAI metadata to Yandex labels.

        Both use the same format (key-value pairs), just different naming.
        """
        return metadata

    @classmethod
    def map_file_create_params(
        cls,
        params: OpenAIFileCreateParams
    ) -> dict:
        """
        Map OpenAI file create parameters to Yandex SDK upload_bytes parameters.

        Returns dict suitable for unpacking into sdk.files.upload_bytes(**result)

        Dropped parameters (not in OpenAI API):
        - description: Not supported in OpenAI
        - labels: Not supported for files in OpenAI (only for vector stores)

        Note: mime_type is NOT set - server auto-detects it from file content.
        """
        return {
            "name": params.name,
            # mime_type is omitted - server auto-detects from content
            "ttl_days": cls.convert_seconds_to_days(params.expires_after_seconds),
            "expiration_policy": cls.convert_anchor_to_policy(params.expires_after_anchor),
        }

    @classmethod
    def map_vector_store_create_params(
        cls,
        params: OpenAIVectorStoreCreateParams
    ) -> dict:
        """
        Map OpenAI vector store create parameters to Yandex SDK search_index parameters.

        Returns dict suitable for unpacking into sdk.search_indexes.create(**result)

        Dropped parameters (not in OpenAI API):
        - description: Not supported in OpenAI
        - index_type: Always vector in OpenAI (no text/hybrid distinction)
        """
        return {
            "name": params.name,
            "labels": cls.convert_metadata_to_labels(params.metadata),
            "ttl_days": params.expires_after_days,
            "expiration_policy": cls.convert_anchor_to_policy(params.expires_after_anchor),
        }

    @classmethod
    def create_legacy_upload_config(
        cls,
        file_create_params: OpenAIFileCreateParams,
        vector_store_create_params: OpenAIVectorStoreCreateParams,
        skip_on_error: bool,
        max_concurrent_uploads: int,
    ) -> UploadConfig:
        """
        Create UploadConfig from OpenAI create parameters for legacy Yandex SDK.

        This method bridges OpenAI params to old UploadConfig structure.
        It will be removed when we switch to native OpenAI API implementation.

        Args:
            file_create_params: OpenAI-compatible file creation parameters
            vector_store_create_params: OpenAI-compatible vector store creation parameters
            skip_on_error: Whether to skip failed files
            max_concurrent_uploads: Maximum concurrent upload tasks

        Returns:
            UploadConfig for legacy Yandex SDK uploader
        """
        return UploadConfig(
            # File settings (mapped from OpenAI)
            file_ttl_days=cls.convert_seconds_to_days(file_create_params.expires_after_seconds),
            file_expiration_policy=cls.convert_anchor_to_policy(file_create_params.expires_after_anchor),
            file_labels=None,  # Not in OpenAI API

            # Index settings (mapped from OpenAI)
            index_name=vector_store_create_params.name,
            index_description=None,  # Not in OpenAI API
            index_labels=cls.convert_metadata_to_labels(vector_store_create_params.metadata),
            index_ttl_days=vector_store_create_params.expires_after_days,
            index_expiration_policy=cls.convert_anchor_to_policy(
                vector_store_create_params.expires_after_anchor
            ),
            index_type=vector_store_create_params.chunking_strategy,

            # Upload behavior
            skip_on_error=skip_on_error,
            max_concurrent_uploads=max_concurrent_uploads,
        )
