"""FAISS-backed retrieval-augmented generation for codebase and documentation search."""

from server.rag.indexer import CodebaseIndexer
from server.rag.searcher import FaissSearcher

__all__ = ["FaissSearcher", "CodebaseIndexer"]
