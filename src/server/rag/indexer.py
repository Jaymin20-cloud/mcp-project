"""FAISS index builder for codebase and documentation."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import faiss

from server.rag.chunker import TextChunker
from server.rag.embedder import Embedder
from shared.logging import get_logger
from shared.models import DocumentChunk

logger = get_logger("rag.indexer")

INDEX_FILENAME = "codebase.index"
METADATA_FILENAME = "metadata.pkl"
MANIFEST_FILENAME = "manifest.json"


class CodebaseIndexer:
    """Walk a directory tree, chunk files, embed, and persist a FAISS index."""

    def __init__(
        self,
        index_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        supported_extensions: list[str] | None = None,
        exclude_dirs: list[str] | None = None,
    ) -> None:
        self.index_path = Path(index_path)
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedder = Embedder(model_name=embedding_model)
        self.supported_extensions = supported_extensions or [".py", ".md", ".txt"]
        self.exclude_dirs = set(exclude_dirs or [".git", "node_modules", "__pycache__"])

    def index_directory(self, root: Path) -> dict:
        """Index all supported files under root and return a summary."""
        root = Path(root).resolve()
        self.index_path.mkdir(parents=True, exist_ok=True)

        all_chunks: list[DocumentChunk] = []
        files_indexed = 0

        for file_path in self._iter_files(root):
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                chunks = self.chunker.chunk_file(file_path.relative_to(root), content)
                all_chunks.extend(chunks)
                files_indexed += 1
            except OSError as exc:
                logger.warning("Skipping %s: %s", file_path, exc)

        if not all_chunks:
            logger.warning("No chunks extracted from %s", root)
            return {"files_indexed": 0, "chunks_indexed": 0}

        texts = [c.content for c in all_chunks]
        embeddings = self.embedder.embed_texts(texts)

        index = faiss.IndexFlatIP(self.embedder.dimension)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        faiss.write_index(index, str(self.index_path / INDEX_FILENAME))
        with open(self.index_path / METADATA_FILENAME, "wb") as f:
            pickle.dump(all_chunks, f)

        manifest = {
            "root": str(root),
            "files_indexed": files_indexed,
            "chunks_indexed": len(all_chunks),
            "embedding_model": self.embedder.model.get_sentence_embedding_dimension(),
            "dimension": self.embedder.dimension,
        }
        with open(self.index_path / MANIFEST_FILENAME, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info("Indexed %d files, %d chunks", files_indexed, len(all_chunks))
        return manifest

    def _iter_files(self, root: Path):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            if path.suffix.lower() in self.supported_extensions:
                yield path
