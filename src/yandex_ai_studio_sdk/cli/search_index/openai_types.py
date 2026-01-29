from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from yandex_ai_studio_sdk.search_indexes import HybridSearchIndexType, TextSearchIndexType, VectorSearchIndexType

ExpiresAfterAnchor = Literal["created_at", "last_active_at"]


@dataclass
class OpenAIFileCreateParams:
    """Parameters for file creation (OpenAI-compatible)."""

    name: str | None = None
    """File name"""

    purpose: str = "assistants"
    """Purpose of the file (always 'assistants' for vector stores)"""

    expires_after_seconds: int | None = None
    """Expiration time in seconds"""

    expires_after_anchor: ExpiresAfterAnchor | None = None
    """When to start counting expiration: 'created_at' or 'last_active_at'"""

    # Note: format/MIME type is NOT included - server auto-detects it


@dataclass
class OpenAIVectorStoreCreateParams:
    """Parameters for vector store creation (OpenAI-compatible)."""

    name: str | None = None
    """Vector store name"""

    metadata: dict[str, str] | None = None
    """Key-value metadata (max 16 pairs)"""

    expires_after_days: int | None = None
    """Expiration time in days"""

    expires_after_anchor: ExpiresAfterAnchor | None = None
    """When to start counting expiration"""

    chunking_strategy: (
        TextSearchIndexType | VectorSearchIndexType | HybridSearchIndexType | None
    ) = None
    """Chunking strategy configuration"""
