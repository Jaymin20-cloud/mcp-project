# MCP Project

A Model Context Protocol (MCP) system featuring FAISS-backed codebase RAG search, GitHub tooling, and a multi-server MCP client that orchestrates Claude tool-use with full call tracing. Containerized with Docker and CI/CD via GitHub Actions.

## Features

### MCP Server
- **FAISS RAG Search** — Semantic search over indexed codebase and documentation
- **GitHub Tools** — Repository info, issues, PRs, file contents, and search
- **FastMCP** — Built on the official MCP Python SDK

### MCP Client
- **Multi-Server Orchestration** — Connect to multiple MCP servers simultaneously
- **Claude Tool-Use** — Automatic tool routing via Anthropic API
- **Full Call Tracing** — JSON traces with timing, inputs, outputs, and errors

### Infrastructure
- **Docker** — Multi-stage build with compose profiles for server, client, and indexer
- **CI/CD** — GitHub Actions for lint, test, Docker build, and GHCR publish

## Quick Start

```bash
# Install
pip install -e ".[rag,dev]"

# Configure
cp .env.example .env   # Add your API keys

# Index codebase
PYTHONPATH=src python -m scripts.index_codebase .

# Run server
PYTHONPATH=src python -m server.main

# Run client
PYTHONPATH=src python -m client.main --query "Find the server entry point"
```

## Project Structure

```
├── config/              # Server configs and settings
├── src/
│   ├── server/          # MCP server (RAG + GitHub)
│   │   ├── rag/         # FAISS indexing and search
│   │   └── github/      # GitHub API tools
│   ├── client/          # Multi-server MCP client
│   │   ├── orchestrator.py
│   │   ├── claude_agent.py
│   │   └── tracing.py
│   ├── shared/          # Shared models and logging
│   └── scripts/         # Indexing CLI
├── tests/               # Unit tests
├── scripts/             # Shell entry points
├── docs/                # Architecture and setup guides
├── Dockerfile
└── docker-compose.yml
```

## Available MCP Tools

### RAG Search
| Tool | Description |
|------|-------------|
| `search_codebase` | Semantic search over indexed files |
| `search_file_content` | Search with optional file path filter |
| `get_index_stats` | Index statistics and manifest |

### GitHub
| Tool | Description |
|------|-------------|
| `github_get_repo` | Repository metadata |
| `github_list_issues` | List repository issues |
| `github_list_pull_requests` | List pull requests |
| `github_search_repos` | Search repositories |
| `github_get_file` | Read file contents |
| `github_list_directory` | List directory contents |

## Documentation

- [Architecture](docs/architecture.md) — System design and data flow
- [Setup Guide](docs/setup.md) — Installation and configuration

## License

MIT
