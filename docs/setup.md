# Setup Guide

## Prerequisites

- Python 3.11+
- pip or uv
- Docker (optional, for containerized deployment)
- Anthropic API key (for client)
- GitHub token (for GitHub tools)

## Local Development

### 1. Clone and install

```bash
cd "MCP Project"
python -m venv .venv
source .venv/bin/activate
pip install -e ".[rag,dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Index your codebase

```bash
export PYTHONPATH=src
python -m scripts.index_codebase .
```

### 4. Run the MCP server

```bash
python -m server.main
```

### 5. Run the MCP client

```bash
# Single query
python -m client.main --query "Search for the main entry point"

# Interactive mode
python -m client.main --interactive

# List available tools
python -m client.main --list-tools
```

## Docker

### Build and run server

```bash
docker compose build
docker compose up mcp-server
```

### Index via Docker

```bash
docker compose --profile index run --rm indexer
```

### Run client via Docker

```bash
docker compose --profile client run --rm mcp-client
```

## Claude Desktop Integration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "codebase-rag": {
      "command": "python",
      "args": ["-m", "server.main"],
      "env": {
        "PYTHONPATH": "/path/to/MCP Project/src",
        "GITHUB_TOKEN": "your-token",
        "RAG_INDEX_PATH": "/path/to/MCP Project/data/index"
      }
    }
  }
}
```

## Running Tests

```bash
export PYTHONPATH=src
pytest tests/ -v
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Index not loaded" | Run `index_codebase` first |
| "GITHUB_TOKEN not set" | Add token to `.env` |
| "ANTHROPIC_API_KEY required" | Add key to `.env` for client |
| Slow first run | Embedding model downloads on first use (~80MB) |
