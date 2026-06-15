# MCP Project — Architecture

## Overview

This project implements a full-stack Model Context Protocol (MCP) system with three main components:

1. **MCP Server** — Exposes FAISS-backed RAG search and GitHub API tools
2. **MCP Client** — Multi-server orchestrator with Claude tool-use and full call tracing
3. **Infrastructure** — Docker containerization and GitHub Actions CI/CD

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │ Claude Agent │──│  Orchestrator   │──│ Trace Collector  │   │
│  └──────────────┘  └────────┬────────┘  └──────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │ stdio transport
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Server                               │
│  ┌──────────────────┐         ┌──────────────────────────┐     │
│  │   RAG Tools      │         │    GitHub Tools          │     │
│  │  ┌────────────┐  │         │  ┌────────────────────┐  │     │
│  │  │  FAISS     │  │         │  │  PyGithub Client   │  │     │
│  │  │  Searcher  │  │         │  └────────────────────┘  │     │
│  │  └────────────┘  │         └──────────────────────────┘     │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
├── config/                  # Configuration files
│   ├── mcp_servers.json     # MCP server connection definitions
│   └── settings.yaml        # Application settings
├── src/
│   ├── server/              # MCP Server
│   │   ├── rag/             # FAISS RAG module
│   │   │   ├── chunker.py   # Text chunking
│   │   │   ├── embedder.py  # Sentence-transformer embeddings
│   │   │   ├── indexer.py   # FAISS index builder
│   │   │   ├── searcher.py  # Semantic search
│   │   │   └── tools.py     # MCP tool definitions
│   │   └── github/          # GitHub integration
│   │       ├── client.py    # PyGithub wrapper
│   │       └── tools.py     # MCP tool definitions
│   ├── client/              # MCP Client
│   │   ├── orchestrator.py  # Multi-server connection manager
│   │   ├── claude_agent.py  # Claude tool-use loop
│   │   └── tracing.py       # Full call tracing
│   ├── shared/              # Shared models and utilities
│   └── scripts/             # CLI utilities
├── tests/                   # Unit and integration tests
├── scripts/                 # Shell entry points
├── data/                    # FAISS index storage
├── traces/                  # Client trace output
└── .github/workflows/       # CI/CD pipelines
```

## Data Flow

### Indexing Pipeline

1. `index_codebase` walks the target directory
2. `TextChunker` splits files into overlapping chunks
3. `Embedder` generates vectors via sentence-transformers
4. `CodebaseIndexer` builds and persists a FAISS index

### Search Pipeline

1. User query is embedded with the same model
2. FAISS performs inner-product similarity search
3. Top-k chunks are returned with scores and source metadata

### Client Orchestration

1. Client connects to configured MCP servers via stdio
2. All tools are aggregated and registered with Claude
3. Claude decides which tools to call based on user query
4. Orchestrator routes tool calls to the correct server
5. Every call is traced with timing, inputs, and outputs

## Trace Format

Traces are saved as JSON files in `traces/` with the following event types:

| Event | Description |
|-------|-------------|
| `session_start` | Client session begins |
| `server_connect` | MCP server connected |
| `tool_call_start` | Tool invocation started |
| `tool_call_end` | Tool invocation completed |
| `llm_request` | Message sent to Claude |
| `llm_response` | Response received from Claude |
| `server_disconnect` | MCP server disconnected |
| `session_end` | Client session ends |
