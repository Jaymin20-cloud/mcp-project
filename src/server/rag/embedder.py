"""Sentence-transformer embedding generation."""

from __future__ import annotations

import numpy as np

from shared.logging import get_logger

logger = get_logger("rag.embedder")


class Embedder:
    """Wraps sentence-transformers for consistent embedding generation."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for RAG. "
                'Install with: pip install "mcp-project[rag]"'
            ) from exc

        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of text strings into a float32 numpy array."""
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.dimension)
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single search query."""
        return self.embed_texts([query])[0]
