"""Claude agent loop with MCP tool-use orchestration."""

from __future__ import annotations

from typing import Any

import anthropic

from client.config import ClientSettings
from client.orchestrator import MCPOrchestrator
from client.tracing import TraceCollector
from shared.logging import get_logger
from shared.models import TraceEventType

logger = get_logger("client.claude_agent")


class ClaudeAgent:
    """Orchestrates Claude tool-use across multiple MCP servers."""

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        settings: ClientSettings,
        tracer: TraceCollector | None = None,
    ) -> None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.orchestrator = orchestrator
        self.tracer = tracer or orchestrator.tracer
        self.max_iterations = settings.max_tool_iterations

    async def run(self, user_message: str, system_prompt: str = "") -> str:
        """Run the agent loop: send message to Claude, execute tools, repeat."""
        tools = self.orchestrator.get_all_tools()
        if not tools:
            logger.warning("No tools available from connected MCP servers")

        default_system = (
            "You are a helpful assistant with access to MCP tools for codebase search "
            "and GitHub operations. Use tools when they would help answer the user's question. "
            "Be concise and accurate."
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
        self.tracer.record(
            TraceEventType.LLM_REQUEST,
            input_data={"message": user_message, "tool_count": len(tools)},
        )

        for iteration in range(self.max_iterations):
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": messages,
                "system": system_prompt or default_system,
            }
            if tools:
                kwargs["tools"] = tools

            response = self.client.messages.create(**kwargs)

            self.tracer.record(
                TraceEventType.LLM_RESPONSE,
                output_data={
                    "stop_reason": response.stop_reason,
                    "iteration": iteration,
                    "content_blocks": len(response.content),
                },
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info("Calling tool: %s", block.name)
                        try:
                            result_text = await self.orchestrator.call_tool(
                                block.name, block.input
                            )
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_text,
                                }
                            )
                        except Exception as exc:
                            logger.error("Tool call failed: %s", exc)
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {exc}",
                                    "is_error": True,
                                }
                            )

                messages.append({"role": "user", "content": tool_results})
                continue

            return self._extract_text(response)

        return "Maximum tool iterations reached. Please try a simpler query."

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else "(no text response)"
