import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import Source, Tool, ToolError, ToolRegistry, ToolRouter  # noqa: E402


class FakeTool(Tool):
    """Fails `fail_times` times (optionally non-retryable), then returns `results`."""

    def __init__(self, name, category="web_search", priority=10, results=None,
                 fail_times=0, retryable=True, delay=0.0, available=True, timeout=5.0):
        self.name, self.category, self.priority = name, category, priority
        self.results = results if results is not None else [Source(title=f"{name} result", url=f"https://{name}.example/1")]
        self.fail_times, self.retryable, self.delay = fail_times, retryable, delay
        self._available, self.timeout = available, timeout
        self.calls = []

    def available(self):
        return self._available

    def _run(self, tool_input):
        self.calls.append((time.monotonic(), tool_input))
        if self.delay:
            time.sleep(self.delay)
        if len(self.calls) <= self.fail_times:
            raise ToolError(f"{self.name} failure {len(self.calls)}", retryable=self.retryable)
        return [Source(**{**s.to_dict(), "tool": ""}) for s in self.results]


def make_router(*tools, **kwargs):
    registry = ToolRegistry()
    for t in tools:
        registry.register(t)
    kwargs.setdefault("sleep", lambda s: None)
    return ToolRouter(registry, **kwargs)


@pytest.fixture
def fake_tool():
    return FakeTool


@pytest.fixture
def router_factory():
    return make_router
