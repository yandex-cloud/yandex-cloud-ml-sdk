"""Utility functions for vector store management."""

from __future__ import annotations

from typing import Any, Dict, List


def create_vector_store(name: str, files: list[str], metadata: dict[str, str]) -> str:
    """
    Create a new vector store with the given files.

    Args:
        name: Vector store name
        files: List of file paths to upload
        metadata: Key-value metadata pairs

    Returns:
        Vector store ID

    Example:
        >>> store_id = create_vector_store(
        ...     name="docs",
        ...     files=["readme.md", "guide.pdf"],
        ...     metadata={"project": "demo"}
        ... )
        Creating vector store 'docs' with 2 files
        >>> print(f"Created: {store_id}")
        Created: vs_abc123
    """
    print(f"Creating vector store '{name}' with {len(files)} files")
    # Implementation here
    return "vs_abc123"


def chunk_text(text: str, max_tokens: int = 800, overlap: int = 400) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Number of overlapping tokens

    Returns:
        List of text chunks
    """
    chunks = []
    # Simple word-based chunking for demo
    words = text.split()
    step = max_tokens - overlap

    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + max_tokens])
        chunks.append(chunk)

    return chunks


class VectorStoreManager:
    """Manager for vector store operations."""

    def __init__(self, folder_id: str, api_key: str):
        self.folder_id = folder_id
        self.api_key = api_key
        self.stores: dict[str, Any] = {}

    def list_stores(self) -> list[str]:
        """List all vector stores."""
        return list(self.stores.keys())

    def delete_store(self, store_id: str) -> bool:
        """Delete a vector store by ID."""
        if store_id in self.stores:
            del self.stores[store_id]
            return True
        return False
