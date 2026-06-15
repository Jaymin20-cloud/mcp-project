"""Unit tests for shared Pydantic models."""

from __future__ import annotations

from shared.models import DocumentChunk, SearchResponse, SearchResult, TraceEvent, TraceEventType


class TestModels:
    def test_document_chunk(self):
        chunk = DocumentChunk(
            chunk_id="abc123",
            source_path="src/main.py",
            content="def main(): pass",
            start_line=1,
            end_line=1,
            chunk_index=0,
        )
        assert chunk.chunk_id == "abc123"

    def test_search_response(self):
        result = SearchResult(
            chunk_id="x",
            source_path="file.py",
            content="code",
            score=0.95,
            start_line=1,
            end_line=10,
        )
        response = SearchResponse(query="test", results=[result], total_results=1)
        assert response.total_results == 1

    def test_trace_event(self):
        event = TraceEvent(
            event_id="e1",
            session_id="s1",
            event_type=TraceEventType.SESSION_START,
        )
        assert event.event_type == TraceEventType.SESSION_START
