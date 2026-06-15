"""MCP server entry point — exposes FAISS RAG search and GitHub tools."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from server.config import get_settings
from server.github.client import GitHubClient
from server.github.tools import register_github_tools
from server.rag.searcher import FaissSearcher
from server.rag.tools import register_rag_tools
from shared.logging import get_logger, setup_logging

logger = get_logger("server.main")


@dataclass
class ServerContext:
    """Shared state available to all MCP tools during server lifetime."""

    searcher: FaissSearcher
    github: GitHubClient | None


def create_server() -> FastMCP:
    """Build and configure the FastMCP server with all tools registered."""
    settings = get_settings()
    setup_logging(settings.log_level)

    searcher = FaissSearcher(
        index_path=settings.rag_index_path,
        embedding_model=settings.rag_embedding_model,
        top_k=settings.rag_top_k,
    )
    searcher.load()

    github_client: GitHubClient | None = None
    if settings.github_token:
        try:
            github_client = GitHubClient(
                token=settings.github_token,
                per_page=settings.github_default_per_page,
            )
            logger.info("GitHub client initialized")
        except ValueError as exc:
            logger.warning("GitHub client not available: %s", exc)
    else:
        logger.warning("GITHUB_TOKEN not set — GitHub tools will be unavailable")

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
        ctx = ServerContext(searcher=searcher, github=github_client)
        logger.info(
            "Server started — index loaded: %s (%d chunks)",
            searcher.is_loaded,
            searcher.chunk_count,
        )
        yield ctx
        logger.info("Server shutting down")

    mcp = FastMCP(settings.mcp_server_name, lifespan=lifespan)

    register_rag_tools(mcp, searcher)
    register_github_tools(mcp, github_client)

    return mcp


def main() -> None:
    """Run the MCP server."""
    mcp = create_server()
    transport = sys.argv[1] if len(sys.argv) > 1 else get_settings().mcp_transport
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
