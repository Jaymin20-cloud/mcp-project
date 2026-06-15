"""MCP tool definitions for GitHub operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from server.github.client import GitHubClient


def register_github_tools(mcp, client: GitHubClient | None) -> None:
    """Register GitHub tools on a FastMCP server instance."""

    def _require_client() -> GitHubClient:
        if client is None:
            raise RuntimeError("GitHub tools unavailable: GITHUB_TOKEN not configured")
        return client

    @mcp.tool()
    def github_get_repo(owner: str, repo: str) -> str:
        """Get metadata about a GitHub repository.

        Args:
            owner: Repository owner (user or organization).
            repo: Repository name.
        """
        info = _require_client().get_repo(owner, repo)
        return json.dumps(info.model_dump(), indent=2)

    @mcp.tool()
    def github_list_issues(
        owner: str,
        repo: str,
        state: str = "open",
        labels: str = "",
        limit: int = 10,
    ) -> str:
        """List issues for a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state filter (open, closed, all).
            labels: Comma-separated label filter.
            limit: Maximum number of issues to return.
        """
        issues = _require_client().list_issues(owner, repo, state, labels or None, limit)
        return json.dumps([i.model_dump() for i in issues], indent=2)

    @mcp.tool()
    def github_list_pull_requests(
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> str:
        """List pull requests for a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: PR state filter (open, closed, all).
            limit: Maximum number of PRs to return.
        """
        prs = _require_client().list_pull_requests(owner, repo, state, limit)
        return json.dumps([p.model_dump() for p in prs], indent=2)

    @mcp.tool()
    def github_search_repos(query: str, limit: int = 10) -> str:
        """Search GitHub repositories.

        Args:
            query: GitHub search query (e.g. 'language:python stars:>100').
            limit: Maximum number of results.
        """
        repos = _require_client().search_repositories(query, limit)
        return json.dumps([r.model_dump() for r in repos], indent=2)

    @mcp.tool()
    def github_get_file(owner: str, repo: str, path: str, ref: str = "") -> str:
        """Get the contents of a file from a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: File path within the repository.
            ref: Git ref (branch, tag, or commit SHA). Defaults to default branch.
        """
        return _require_client().get_file_content(owner, repo, path, ref)

    @mcp.tool()
    def github_list_directory(owner: str, repo: str, path: str = "", ref: str = "") -> str:
        """List contents of a directory in a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: Directory path (empty for root).
            ref: Git ref (branch, tag, or commit SHA).
        """
        entries = _require_client().list_directory(owner, repo, path, ref)
        return json.dumps(entries, indent=2)
