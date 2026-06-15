"""Unit tests for trace collection."""

from __future__ import annotations

from client.tracing import TraceCollector
from shared.models import TraceEventType


class TestTraceCollector:
    def test_record_event(self, temp_dir):
        tracer = TraceCollector(output_dir=temp_dir)
        event = tracer.record(
            TraceEventType.TOOL_CALL_START,
            server_name="test-server",
            tool_name="search_codebase",
            input_data={"query": "test"},
        )
        assert event.session_id == tracer.session_id
        assert len(tracer.events) == 1

    def test_timed_tool_call_success(self, temp_dir):
        tracer = TraceCollector(output_dir=temp_dir)
        with tracer.timed_tool_call("server", "tool", {"arg": "val"}):
            pass
        end_events = [e for e in tracer.events if e.event_type == TraceEventType.TOOL_CALL_END]
        assert len(end_events) == 1
        assert end_events[0].duration_ms is not None
        assert end_events[0].error is None

    def test_timed_tool_call_error(self, temp_dir):
        tracer = TraceCollector(output_dir=temp_dir)
        try:
            with tracer.timed_tool_call("server", "tool", {}):
                raise ValueError("test error")
        except ValueError:
            pass
        end_events = [e for e in tracer.events if e.event_type == TraceEventType.TOOL_CALL_END]
        assert end_events[0].error == "test error"

    def test_save_trace(self, temp_dir):
        tracer = TraceCollector(output_dir=temp_dir)
        tracer.session_start()
        tracer.record(TraceEventType.TOOL_CALL_START, tool_name="test")
        tracer.session_end()

        path = tracer.save()
        assert path.exists()
        assert path.suffix == ".json"

    def test_summary(self, temp_dir):
        tracer = TraceCollector(output_dir=temp_dir)
        tracer.session_start()
        with tracer.timed_tool_call("s", "t", {}):
            pass
        tracer.session_end()

        summary = tracer.summary()
        assert summary["tool_calls"] == 1
        assert summary["total_events"] >= 3
