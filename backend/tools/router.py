"""Routes a subtask to a tool, with retry and fallback.

For a category, the router tries each available tool in priority order. Each tool
gets up to `max_attempts` tries with exponential backoff (base_delay, 2x, 4x, ...
plus jitter) and a hard per-call timeout. If a tool still fails, or returns no
results, the router falls back to the next tool in the category. Every attempt is
recorded in the result so the report and logs show what happened.
"""

import asyncio
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .base import Source, ToolError
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class Attempt:
    tool: str
    attempt: int
    ok: bool
    error: str = ""
    duration_ms: int = 0


@dataclass
class RouteResult:
    category: str
    tool_used: Optional[str]
    results: List[Source] = field(default_factory=list)
    attempts: List[Attempt] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.tool_used is not None

    def to_dict(self):
        return {
            "category": self.category,
            "tool_used": self.tool_used,
            "results": [r.to_dict() for r in self.results],
            "attempts": [a.__dict__ for a in self.attempts],
        }


class ToolRouter:
    def __init__(
        self,
        registry: ToolRegistry,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 8.0,
        fallback_on_empty: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        max_workers: int = 16,
    ):
        self.registry = registry
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.fallback_on_empty = fallback_on_empty
        self._sleep = sleep
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="tool")

    def backoff(self, attempt: int) -> float:
        """Delay before retry number `attempt` (1-based): base * 2^(attempt-1), capped, with up to 10% jitter."""
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        return delay + random.uniform(0, delay * 0.1)

    def run(self, category: str, tool_input: str, prefer: Optional[str] = None) -> RouteResult:
        tools = [t for t in self.registry.by_category(category) if t.available()]
        if prefer:
            tools.sort(key=lambda t: t.name != prefer)
        result = RouteResult(category=category, tool_used=None)
        if not tools:
            logger.warning("No available tools for category %s", category)
            return result

        for tool in tools:
            for attempt in range(1, self.max_attempts + 1):
                start = time.monotonic()
                try:
                    future = self._pool.submit(tool.run, tool_input)
                    sources = future.result(timeout=tool.timeout)
                except FutureTimeout:
                    err, retryable = f"timed out after {tool.timeout}s", True
                except ToolError as e:
                    err, retryable = str(e), e.retryable
                except Exception as e:  # network errors, parsing errors, bugs in a tool
                    err, retryable = f"{type(e).__name__}: {e}", True
                else:
                    ms = int((time.monotonic() - start) * 1000)
                    if sources or not self.fallback_on_empty:
                        result.attempts.append(Attempt(tool.name, attempt, True, duration_ms=ms))
                        result.tool_used = tool.name
                        result.results = sources
                        return result
                    # Empty results: retrying the same query won't help, so move to the next tool.
                    result.attempts.append(Attempt(tool.name, attempt, False, "no results", ms))
                    break

                ms = int((time.monotonic() - start) * 1000)
                result.attempts.append(Attempt(tool.name, attempt, False, err, ms))
                logger.info("%s attempt %d failed: %s", tool.name, attempt, err)
                if not retryable or attempt == self.max_attempts:
                    break
                self._sleep(self.backoff(attempt))
            logger.info("Falling back from %s in %s", tool.name, category)

        return result

    async def arun(self, category: str, tool_input: str, prefer: Optional[str] = None) -> RouteResult:
        """Async wrapper so many routed calls can be awaited together with asyncio.gather."""
        return await asyncio.to_thread(self.run, category, tool_input, prefer)
