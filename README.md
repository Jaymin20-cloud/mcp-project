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

## Demo

A single query flows through the client → MCP server → FAISS search → Claude synthesis, with every step captured in a trace file.

### 1. Run a query

```bash
$ PYTHONPATH=src python -m client.main --query "Find the server entry point"
```

### 2. What happens under the hood

```
[19:04:12] INFO  Connected to 'codebase-rag' with 9 tools
[19:04:13] INFO  Calling tool: codebase-rag__search_codebase
[19:04:14] INFO  Session complete — 1 tool calls, trace: ./traces/trace_a3f8b2c1_20260615_190414.json
```

Claude receives the query, selects the RAG tool, and the orchestrator routes the call to the `codebase-rag` MCP server:

| Step | Actor | Action |
|------|-------|--------|
| 1 | Client | Connects to `codebase-rag` via stdio, aggregates 9 tools |
| 2 | Claude | Decides to call `codebase-rag__search_codebase` |
| 3 | MCP Server | Runs FAISS semantic search over the indexed codebase |
| 4 | Claude | Reads tool results and writes the final answer |

**Tool call** (routed to `search_codebase` on the server):

```json
{
  "tool": "codebase-rag__search_codebase",
  "arguments": { "query": "server entry point main function", "top_k": 3 }
}
```

**Tool result** (top hit from `src/server/main.py`):

```
Search results for: server entry point main function
Found 3 matches:

--- Result 1 (score: 0.891) ---
File: src/server/main.py (lines 74-82)
def main() -> None:
    """Run the MCP server."""
    mcp = create_server()
    transport = sys.argv[1] if len(sys.argv) > 1 else get_settings().mcp_transport
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
```

### 3. Claude's answer (printed to stdout)

```
The server entry point is `src/server/main.py`. The `main()` function creates
the FastMCP server via `create_server()`, reads the transport from argv or
config (default: stdio), and calls `mcp.run()`. Run it with:

  PYTHONPATH=src python -m server.main
```

### 4. Trace JSON (saved to `./traces/`)

Every session writes a full audit log — tool inputs, timings, LLM round-trips:

```json
{
  "session_id": "a3f8b2c1-7e4d-4a9b-9c12-8f6d0e5a1b23",
  "total_events": 7,
  "events": [
    { "event_type": "session_start", "metadata": { "mode": "single" } },
    {
      "event_type": "server_connect",
      "server_name": "codebase-rag",
      "metadata": { "tools": ["search_codebase", "get_index_stats", "search_file_content", "..."] }
    },
    {
      "event_type": "llm_request",
      "input_data": { "message": "Find the server entry point", "tool_count": 9 }
    },
    {
      "event_type": "tool_call_start",
      "server_name": "codebase-rag",
      "tool_name": "search_codebase",
      "input_data": { "query": "server entry point main function", "top_k": 3 }
    },
    {
      "event_type": "tool_call_end",
      "server_name": "codebase-rag",
      "tool_name": "search_codebase",
      "duration_ms": 142.3,
      "metadata": { "success": true }
    },
    {
      "event_type": "llm_response",
      "output_data": { "stop_reason": "end_turn", "iteration": 1 }
    },
    { "event_type": "session_end", "duration_ms": 2847.1, "metadata": { "total_events": 7 } }
  ]
}
```

Try interactive mode to explore further:

```bash
PYTHONPATH=src python -m client.main --interactive
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
