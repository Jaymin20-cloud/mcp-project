"""FAISS similarity search over indexed codebase chunks."""

from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np

from server.rag.embedder import Embedder
from server.rag.indexer import INDEX_FILENAME, MANIFEST_FILENAME, METADATA_FILENAME
from shared.logging import get_logger
from shared.models import DocumentChunk, SearchResponse, SearchResult

logger = get_logger("rag.searcher")


class FaissSearcher:
    """Load a persisted FAISS index and run semantic search queries."""

    def __init__(
        self,
        index_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        top_k: int = 5,
    ) -> None:
        self.index_path = Path(index_path)
        self.top_k = top_k
        self.embedder = Embedder(model_name=embedding_model)
        self._index: faiss.Index | None = None
        self._chunks: list[DocumentChunk] = []
        self._loaded = False

    def load(self) -> bool:
        """Load index and metadata from disk. Returns False if not found."""
        index_file = self.index_path / INDEX_FILENAME
        metadata_file = self.index_path / METADATA_FILENAME

        if not index_file.exists() or not metadata_file.exists():
            logger.warning("Index not found at %s", self.index_path)
            return False

        self._index = faiss.read_index(str(index_file))
        with open(metadata_file, "rb") as f:
            self._chunks = pickle.load(f)
        self._loaded = True
        logger.info("Loaded index with %d chunks", len(self._chunks))
        return True

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._index is not None

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def search(self, query: str, top_k: int | None = None) -> SearchResponse:
        """Run a semantic search and return ranked results."""
        if not self.is_loaded:
            raise RuntimeError("Index not loaded. Run indexing first.")

        k = top_k or self.top_k
        query_vec = self.embedder.embed_query(query).reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vec)

        scores, indices = self._index.search(query_vec, min(k, len(self._chunks)))

        results: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0:
                continue
            chunk = self._chunks[idx]
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    content=chunk.content,
                    score=float(score),
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                )
            )

        return SearchResponse(query=query, results=results, total_results=len(results))

    def get_index_stats(self) -> dict:
        """Return summary statistics about the loaded index."""
        manifest_file = self.index_path / MANIFEST_FILENAME
        stats: dict = {
            "loaded": self.is_loaded,
            "chunk_count": self.chunk_count,
            "index_path": str(self.index_path),
        }
        if manifest_file.exists():
            import json

            with open(manifest_file) as f:
                stats["manifest"] = json.load(f)
        return stats
