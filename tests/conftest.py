"""Test configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def mock_sentence_transformer(monkeypatch):
    """Replace SentenceTransformer with a deterministic fake for offline tests."""

    class FakeModel:
        def get_sentence_embedding_dimension(self) -> int:
            return 384

        def encode(self, texts, **kwargs):
            vectors = []
            for text in texts:
                seed = abs(hash(text)) % (2**31)
                rng = np.random.RandomState(seed)
                vectors.append(rng.rand(384).astype(np.float32))
            return np.array(vectors)

    monkeypatch.setattr(
        "server.rag.embedder.SentenceTransformer",
        lambda model_name: FakeModel(),
    )


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_python_file(temp_dir: Path) -> Path:
    content = '''"""Sample module for testing."""

def hello(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"

class Greeter:
    def __init__(self, prefix: str = "Hi"):
        self.prefix = prefix

    def greet(self, name: str) -> str:
        return f"{self.prefix}, {name}!"
'''
    file_path = temp_dir / "sample.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_markdown_file(temp_dir: Path) -> Path:
    content = """# Test Documentation

This is a test document for RAG indexing.

## Features

- Semantic search
- FAISS vector store
- GitHub integration
"""
    file_path = temp_dir / "README.md"
    file_path.write_text(content)
    return file_path
