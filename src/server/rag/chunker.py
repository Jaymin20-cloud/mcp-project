"""Text chunking utilities for RAG indexing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from shared.models import DocumentChunk


class TextChunker:
    """Split source files into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, file_path: Path, content: str) -> list[DocumentChunk]:
        """Split file content into line-aware chunks."""
        lines = content.splitlines()
        if not lines:
            return []

        chunks: list[DocumentChunk] = []
        char_buffer = ""
        start_line = 1
        current_line = 1
        chunk_index = 0

        for line in lines:
            char_buffer += line + "\n"
            current_line += 1

            if len(char_buffer) >= self.chunk_size:
                chunk_id = self._make_chunk_id(str(file_path), chunk_index)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_path=str(file_path),
                        content=char_buffer.strip(),
                        start_line=start_line,
                        end_line=current_line - 1,
                        chunk_index=chunk_index,
                    )
                )
                overlap_text = char_buffer[-self.chunk_overlap :] if self.chunk_overlap else ""
                char_buffer = overlap_text
                start_line = max(1, current_line - overlap_text.count("\n") - 1)
                chunk_index += 1

        if char_buffer.strip():
            chunk_id = self._make_chunk_id(str(file_path), chunk_index)
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_path=str(file_path),
                    content=char_buffer.strip(),
                    start_line=start_line,
                    end_line=current_line - 1,
                    chunk_index=chunk_index,
                )
            )

        return chunks

    @staticmethod
    def _make_chunk_id(source_path: str, chunk_index: int) -> str:
        raw = f"{source_path}:{chunk_index}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
