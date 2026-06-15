"""Unit tests for RAG chunking, indexing, and search."""

from __future__ import annotations

from server.rag.chunker import TextChunker
from server.rag.indexer import CodebaseIndexer
from server.rag.searcher import FaissSearcher


class TestTextChunker:
    def test_chunk_file_produces_chunks(self, sample_python_file):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        content = sample_python_file.read_text()
        chunks = chunker.chunk_file(sample_python_file, content)

        assert len(chunks) >= 1
        assert all(c.source_path == str(sample_python_file) for c in chunks)
        assert all(c.content for c in chunks)

    def test_empty_file_produces_no_chunks(self, temp_dir):
        empty = temp_dir / "empty.py"
        empty.write_text("")
        chunker = TextChunker()
        chunks = chunker.chunk_file(empty, "")
        assert chunks == []

    def test_chunk_ids_are_unique(self, sample_python_file):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        content = sample_python_file.read_text()
        chunks = chunker.chunk_file(sample_python_file, content)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))


class TestCodebaseIndexer:
    def test_index_directory(
        self, temp_dir, sample_python_file, sample_markdown_file, mock_sentence_transformer
    ):
        indexer = CodebaseIndexer(
            index_path=temp_dir / "index",
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=256,
            chunk_overlap=32,
            supported_extensions=[".py", ".md"],
        )
        manifest = indexer.index_directory(temp_dir)

        assert manifest["files_indexed"] == 2
        assert manifest["chunks_indexed"] >= 2


class TestFaissSearcher:
    def test_search_returns_results(
        self, temp_dir, sample_python_file, sample_markdown_file, mock_sentence_transformer
    ):
        index_path = temp_dir / "index"
        indexer = CodebaseIndexer(
            index_path=index_path,
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=256,
            supported_extensions=[".py", ".md"],
        )
        indexer.index_directory(temp_dir)

        searcher = FaissSearcher(index_path=index_path, embedding_model="all-MiniLM-L6-v2")
        assert searcher.load()
        assert searcher.is_loaded

        response = searcher.search("greeting function")
        assert response.total_results > 0
        assert response.results[0].score > 0

    def test_search_without_index_raises(self, temp_dir, mock_sentence_transformer):
        searcher = FaissSearcher(index_path=temp_dir / "missing")
        assert not searcher.load()
        assert not searcher.is_loaded
