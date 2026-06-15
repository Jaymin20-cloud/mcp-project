"""Client configuration loaded from environment and config files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
_SERVERS_FILE = _CONFIG_DIR / "mcp_servers.json"
_SETTINGS_FILE = _CONFIG_DIR / "settings.yaml"


def _load_yaml_settings() -> dict:
    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml_settings()


class MCPServerConfig:
    """Configuration for a single MCP server connection."""

    def __init__(self, data: dict) -> None:
        self.name: str = data["name"]
        self.description: str = data.get("description", "")
        self.transport: str = data.get("transport", "stdio")
        self.command: str = data["command"]
        self.args: list[str] = data.get("args", [])
        self.env: dict[str, str] = data.get("env", {})
        self.url: str | None = data.get("url")


def load_server_configs(path: Path | None = None) -> list[MCPServerConfig]:
    """Load MCP server configurations from JSON file."""
    config_path = path or _SERVERS_FILE
    if not config_path.exists():
        return []
    with open(config_path) as f:
        data = json.load(f)
    return [MCPServerConfig(s) for s in data.get("servers", [])]


class ClientSettings(BaseSettings):
    """Environment-backed settings for the MCP client."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-20250514", alias="CLAUDE_MODEL")

    trace_output_dir: Path = Field(default=Path("./traces"), alias="TRACE_OUTPUT_DIR")
    trace_enabled: bool = Field(default=True, alias="TRACE_ENABLED")

    mcp_servers_config: Path = Field(
        default=_SERVERS_FILE,
        alias="MCP_SERVERS_CONFIG",
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def max_tool_iterations(self) -> int:
        return _yaml.get("client", {}).get("max_tool_iterations", 10)


def get_client_settings() -> ClientSettings:
    return ClientSettings()
