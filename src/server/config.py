"""Server configuration loaded from environment and YAML settings."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_SETTINGS_FILE = _CONFIG_DIR / "settings.yaml"


def _load_yaml_settings() -> dict:
    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml_settings()


class ServerSettings(BaseSettings):
    """Environment-backed settings for the MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_name: str = Field(default="codebase-mcp-server", alias="MCP_SERVER_NAME")
    mcp_transport: str = Field(default="stdio", alias="MCP_TRANSPORT")

    rag_index_path: Path = Field(default=Path("./data/index"), alias="RAG_INDEX_PATH")
    rag_embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="RAG_EMBEDDING_MODEL")
    rag_chunk_size: int = Field(default=512, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=64, alias="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")

    github_token: str = Field(default="", alias="GITHUB_TOKEN")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def supported_extensions(self) -> list[str]:
        return _yaml.get("rag", {}).get("supported_extensions", [".py", ".md", ".txt"])

    @property
    def exclude_dirs(self) -> list[str]:
        return _yaml.get("rag", {}).get("exclude_dirs", [".git", "node_modules", "__pycache__"])

    @property
    def github_default_per_page(self) -> int:
        return _yaml.get("github", {}).get("default_per_page", 30)


def get_settings() -> ServerSettings:
    return ServerSettings()
