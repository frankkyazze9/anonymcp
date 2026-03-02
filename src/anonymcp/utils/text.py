"""Text processing utilities."""

from __future__ import annotations


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text for safe logging, preserving word boundaries."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated + "..."


def chunk_text(text: str, max_chunk_size: int = 5000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for processing long documents.

    Args:
        text: The text to chunk.
        max_chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks
