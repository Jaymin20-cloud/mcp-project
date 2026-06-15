"""GitHub API client wrapping PyGithub."""

from __future__ import annotations

from github import Github
from github.GithubException import GithubException

from shared.logging import get_logger
from shared.models import GitHubIssueSummary, GitHubRepoInfo

logger = get_logger("github.client")


class GitHubClient:
    """Thin wrapper around PyGithub for MCP tool operations."""

    def __init__(self, token: str, per_page: int = 30) -> None:
        if not token:
            raise ValueError("GITHUB_TOKEN is required for GitHub tools")
        self._gh = Github(token, per_page=per_page)

    def get_repo(self, owner: str, repo: str) -> GitHubRepoInfo:
        """Fetch repository metadata."""
        try:
            r = self._gh.get_repo(f"{owner}/{repo}")
            return GitHubRepoInfo(
                full_name=r.full_name,
                description=r.description,
                stars=r.stargazers_count,
                forks=r.forks_count,
                language=r.language,
                default_branch=r.default_branch,
                url=r.html_url,
            )
        except GithubException as exc:
            logger.error("Failed to get repo %s/%s: %s", owner, repo, exc)
            raise

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str | None = None,
        limit: int = 10,
    ) -> list[GitHubIssueSummary]:
        """List issues for a repository."""
        try:
            repository = self._gh.get_repo(f"{owner}/{repo}")
            issues = repository.get_issues(state=state, labels=labels or "")
            results: list[GitHubIssueSummary] = []
            for issue in issues:
                if issue.pull_request:
                    continue
                results.append(
                    GitHubIssueSummary(
                        number=issue.number,
                        title=issue.title,
                        state=issue.state,
                        author=issue.user.login if issue.user else "unknown",
                        url=issue.html_url,
                        labels=[lbl.name for lbl in issue.labels],
                        created_at=issue.created_at.isoformat(),
                    )
                )
                if len(results) >= limit:
                    break
            return results
        except GithubException as exc:
            logger.error("Failed to list issues for %s/%s: %s", owner, repo, exc)
            raise

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> list[GitHubIssueSummary]:
        """List pull requests for a repository."""
        try:
            repository = self._gh.get_repo(f"{owner}/{repo}")
            prs = repository.get_pulls(state=state)
            results: list[GitHubIssueSummary] = []
            for pr in prs:
                results.append(
                    GitHubIssueSummary(
                        number=pr.number,
                        title=pr.title,
                        state=pr.state,
                        author=pr.user.login if pr.user else "unknown",
                        url=pr.html_url,
                        labels=[lbl.name for lbl in pr.labels],
                        created_at=pr.created_at.isoformat(),
                    )
                )
                if len(results) >= limit:
                    break
            return results
        except GithubException as exc:
            logger.error("Failed to list PRs for %s/%s: %s", owner, repo, exc)
            raise

    def search_repositories(self, query: str, limit: int = 10) -> list[GitHubRepoInfo]:
        """Search GitHub repositories."""
        try:
            repos = self._gh.search_repositories(query)
            results: list[GitHubRepoInfo] = []
            for repo in repos:
                results.append(
                    GitHubRepoInfo(
                        full_name=repo.full_name,
                        description=repo.description,
                        stars=repo.stargazers_count,
                        forks=repo.forks_count,
                        language=repo.language,
                        default_branch=repo.default_branch,
                        url=repo.html_url,
                    )
                )
                if len(results) >= limit:
                    break
            return results
        except GithubException as exc:
            logger.error("Repository search failed: %s", exc)
            raise

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "") -> str:
        """Get the contents of a file from a GitHub repository."""
        try:
            repository = self._gh.get_repo(f"{owner}/{repo}")
            kwargs = {"path": path}
            if ref:
                kwargs["ref"] = ref
            content = repository.get_contents(path, ref=ref if ref else None)
            if isinstance(content, list):
                return "Error: Path is a directory, not a file"
            return content.decoded_content.decode("utf-8", errors="replace")
        except GithubException as exc:
            logger.error("Failed to get file %s/%s/%s: %s", owner, repo, path, exc)
            raise

    def list_directory(self, owner: str, repo: str, path: str = "", ref: str = "") -> list[dict]:
        """List contents of a directory in a GitHub repository."""
        try:
            repository = self._gh.get_repo(f"{owner}/{repo}")
            contents = repository.get_contents(path or "", ref=ref if ref else None)
            if not isinstance(contents, list):
                return [{"name": contents.name, "path": contents.path, "type": contents.type}]
            return [
                {"name": c.name, "path": c.path, "type": c.type, "size": c.size}
                for c in contents
            ]
        except GithubException as exc:
            logger.error("Failed to list directory %s/%s/%s: %s", owner, repo, path, exc)
            raise
