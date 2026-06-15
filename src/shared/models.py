"""Shared Pydantic models for RAG, tracing, and GitHub responses."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TraceEventType(StrEnum):
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SERVER_CONNECT = "server_connect"
    SERVER_DISCONNECT = "server_disconnect"
    TOOL_LIST = "tool_list"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    ERROR = "error"


class TraceEvent(BaseModel):
    """A single traced event in the MCP client orchestration pipeline."""

    event_id: str
    session_id: str
    event_type: TraceEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    server_name: str | None = None
    tool_name: str | None = None
    duration_ms: float | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A chunk of text extracted from a source file."""

    chunk_id: str
    source_path: str
    content: str
    start_line: int
    end_line: int
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A single RAG search result."""

    chunk_id: str
    source_path: str
    content: str
    score: float
    start_line: int
    end_line: int


class SearchResponse(BaseModel):
    """Response from a RAG search query."""

    query: str
    results: list[SearchResult]
    total_results: int


class GitHubRepoInfo(BaseModel):
    """Summary information about a GitHub repository."""

    full_name: str
    description: str | None
    stars: int
    forks: int
    language: str | None
    default_branch: str
    url: str


class GitHubIssueSummary(BaseModel):
    """Summary of a GitHub issue or pull request."""

    number: int
    title: str
    state: str
    author: str
    url: str
    labels: list[str] = Field(default_factory=list)
    created_at: str
