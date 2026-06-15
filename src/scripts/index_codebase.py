"""CLI script to index a codebase into the FAISS vector store."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from server.config import get_settings
from server.rag.indexer import CodebaseIndexer
from shared.logging import get_logger, setup_logging

logger = get_logger("scripts.index_codebase")


def main() -> None:
    parser = argparse.ArgumentParser(description="Index a codebase for FAISS RAG search")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to index (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output index directory (overrides RAG_INDEX_PATH)",
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level)

    root = Path(args.path).resolve()
    index_path = Path(args.output) if args.output else settings.rag_index_path

    logger.info("Indexing %s -> %s", root, index_path)

    indexer = CodebaseIndexer(
        index_path=index_path,
        embedding_model=settings.rag_embedding_model,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        supported_extensions=settings.supported_extensions,
        exclude_dirs=settings.exclude_dirs,
    )

    manifest = indexer.index_directory(root)
    print(f"Indexing complete: {manifest}")
    sys.exit(0 if manifest.get("chunks_indexed", 0) > 0 else 1)


if __name__ == "__main__":
    main()
