"""Full call tracing for MCP client orchestration."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.logging import get_logger
from shared.models import TraceEvent, TraceEventType

logger = get_logger("client.tracing")


class TraceCollector:
    """Collects and persists trace events for MCP client sessions."""

    def __init__(self, session_id: str | None = None, output_dir: Path | None = None) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.output_dir = Path(output_dir) if output_dir else Path("./traces")
        self.events: list[TraceEvent] = []
        self._start_time = time.monotonic()

    def record(
        self,
        event_type: TraceEventType,
        server_name: str | None = None,
        tool_name: str | None = None,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceEvent:
        """Record a single trace event."""
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            session_id=self.session_id,
            event_type=event_type,
            server_name=server_name,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self.events.append(event)
        self._log_event(event)
        return event

    def _log_event(self, event: TraceEvent) -> None:
        parts = [f"[{event.event_type.value}]"]
        if event.server_name:
            parts.append(f"server={event.server_name}")
        if event.tool_name:
            parts.append(f"tool={event.tool_name}")
        if event.duration_ms is not None:
            parts.append(f"duration={event.duration_ms:.1f}ms")
        if event.error:
            parts.append(f"error={event.error}")
        logger.debug(" ".join(parts))

    @contextmanager
    def timed_tool_call(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Generator[TraceEvent, None, None]:
        """Context manager that traces a tool call with timing."""
        start = time.monotonic()
        event = self.record(
            TraceEventType.TOOL_CALL_START,
            server_name=server_name,
            tool_name=tool_name,
            input_data=arguments,
        )
        try:
            yield event
            duration = (time.monotonic() - start) * 1000
            self.record(
                TraceEventType.TOOL_CALL_END,
                server_name=server_name,
                tool_name=tool_name,
                duration_ms=duration,
                metadata={"success": True},
            )
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            self.record(
                TraceEventType.TOOL_CALL_END,
                server_name=server_name,
                tool_name=tool_name,
                duration_ms=duration,
                error=str(exc),
                metadata={"success": False},
            )
            raise

    def session_start(self, metadata: dict[str, Any] | None = None) -> TraceEvent:
        return self.record(TraceEventType.SESSION_START, metadata=metadata)

    def session_end(self) -> TraceEvent:
        total_ms = (time.monotonic() - self._start_time) * 1000
        return self.record(
            TraceEventType.SESSION_END,
            duration_ms=total_ms,
            metadata={"total_events": len(self.events)},
        )

    def save(self) -> Path:
        """Persist trace to JSON file and return the path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{self.session_id[:8]}_{timestamp}.json"
        path = self.output_dir / filename

        payload = {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "events": [e.model_dump(mode="json") for e in self.events],
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2, default=str)

        logger.info("Trace saved to %s (%d events)", path, len(self.events))
        return path

    def summary(self) -> dict[str, Any]:
        """Return a summary of the trace session."""
        tool_calls = [e for e in self.events if e.event_type == TraceEventType.TOOL_CALL_END]
        errors = [e for e in self.events if e.error]
        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "tool_calls": len(tool_calls),
            "errors": len(errors),
            "total_duration_ms": sum(e.duration_ms or 0 for e in tool_calls),
        }
