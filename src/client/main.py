"""MCP client CLI — multi-server orchestration with Claude and tracing."""

from __future__ import annotations

import argparse
import asyncio
import sys

from client.claude_agent import ClaudeAgent
from client.config import get_client_settings, load_server_configs
from client.orchestrator import MCPOrchestrator
from client.tracing import TraceCollector
from shared.logging import get_logger, setup_logging

logger = get_logger("client.main")


async def run_interactive(agent: ClaudeAgent, orchestrator: MCPOrchestrator) -> None:
    """Run an interactive REPL session."""
    print("MCP Client — Interactive Mode")
    print(orchestrator.list_tools_summary())
    print("Type 'quit' or 'exit' to end the session.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break

        print("\nAssistant: ", end="", flush=True)
        response = await agent.run(user_input)
        print(response)
        print()


async def run_single_query(agent: ClaudeAgent, query: str) -> str:
    """Run a single query and return the response."""
    return await agent.run(query)


async def async_main(args: argparse.Namespace) -> int:
    """Async entry point for the MCP client."""
    settings = get_client_settings()
    setup_logging(settings.log_level)

    tracer = TraceCollector(output_dir=settings.trace_output_dir)
    tracer.session_start(metadata={"mode": "interactive" if args.interactive else "single"})

    orchestrator = MCPOrchestrator(tracer=tracer)
    server_configs = load_server_configs(settings.mcp_servers_config)

    if not server_configs:
        logger.error("No MCP server configurations found at %s", settings.mcp_servers_config)
        return 1

    try:
        connected = await orchestrator.connect_all(server_configs)
        if not connected:
            logger.error("Failed to connect to any MCP servers")
            return 1

        agent = ClaudeAgent(orchestrator, settings, tracer)

        if args.interactive:
            await run_interactive(agent, orchestrator)
        elif args.query:
            response = await run_single_query(agent, args.query)
            print(response)
        else:
            print(orchestrator.list_tools_summary())
            print("\nUse --query 'your question' or --interactive to start.")

    finally:
        await orchestrator.disconnect_all()
        tracer.session_end()
        if settings.trace_enabled:
            trace_path = tracer.save()
            summary = tracer.summary()
            logger.info(
                "Session complete — %d tool calls, trace: %s",
                summary["tool_calls"],
                trace_path,
            )

    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP multi-server client with Claude orchestration"
    )
    parser.add_argument("-q", "--query", type=str, help="Single query to run")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive REPL mode")
    parser.add_argument("--list-tools", action="store_true", help="List available tools and exit")
    args = parser.parse_args()

    if args.list_tools:
        args.query = None
        args.interactive = False

    sys.exit(asyncio.run(async_main(args)))


if __name__ == "__main__":
    main()
