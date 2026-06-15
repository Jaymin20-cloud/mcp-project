"""Structured logging configuration for the MCP project."""

from __future__ import annotations

import logging

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the root application logger."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    return logging.getLogger("mcp-project")


def get_logger(name: str) -> logging.Logger:
    """Get a named child logger."""
    return logging.getLogger(f"mcp-project.{name}")
