"""MCP tool definitions for RAG search operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shared.models import SearchResponse

if TYPE_CHECKING:
    from server.rag.searcher import FaissSearcher


def format_search_results(response: SearchResponse) -> str:
    """Format search results as readable text for LLM consumption."""
    if not response.results:
        return f"No results found for query: {response.query}"

    lines = [f"Search results for: {response.query}", f"Found {response.total_results} matches:\n"]
    for i, result in enumerate(response.results, 1):
        lines.append(f"--- Result {i} (score: {result.score:.3f}) ---")
        lines.append(f"File: {result.source_path} (lines {result.start_line}-{result.end_line})")
        lines.append(result.content)
        lines.append("")

    return "\n".join(lines)


def register_rag_tools(mcp, searcher: FaissSearcher) -> None:
    """Register RAG search tools on a FastMCP server instance."""

    @mcp.tool()
    def search_codebase(query: str, top_k: int = 5) -> str:
        """Search the indexed codebase and documentation using semantic similarity.

        Args:
            query: Natural language search query describing what you're looking for.
            top_k: Number of results to return (default 5).
        """
        if not searcher.is_loaded:
            return (
                "Error: Search index not loaded. "
                "Run the index_codebase script first to build the FAISS index."
            )
        response = searcher.search(query, top_k=top_k)
        return format_search_results(response)

    @mcp.tool()
    def get_index_stats() -> str:
        """Get statistics about the current FAISS search index."""
        stats = searcher.get_index_stats()
        return json.dumps(stats, indent=2)

    @mcp.tool()
    def search_file_content(query: str, file_pattern: str = "", top_k: int = 3) -> str:
        """Search codebase with optional file path filtering.

        Args:
            query: Natural language search query.
            file_pattern: Optional substring to filter results by file path.
            top_k: Number of results to return.
        """
        if not searcher.is_loaded:
            return "Error: Search index not loaded."

        response = searcher.search(query, top_k=top_k * 3)
        if file_pattern:
            response.results = [r for r in response.results if file_pattern in r.source_path]
            response.results = response.results[:top_k]
            response.total_results = len(response.results)

        return format_search_results(response)
