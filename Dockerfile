# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[rag]"

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/
COPY pyproject.toml README.md ./

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV RAG_INDEX_PATH=/app/data/index
ENV TRACE_OUTPUT_DIR=/app/traces

RUN mkdir -p /app/data/index /app/traces \
    && chmod +x scripts/*.sh

EXPOSE 8000

# Default: run MCP server via stdio (override in docker-compose)
ENTRYPOINT ["python", "-m", "server.main"]
CMD ["stdio"]
