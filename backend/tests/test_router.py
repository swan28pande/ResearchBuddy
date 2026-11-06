import asyncio
import time


def test_success_first_try(fake_tool, router_factory):
    t = fake_tool("a")
    res = router_factory(t).run("web_search", "q")
    assert res.ok and res.tool_used == "a"
    assert res.results[0].tool == "a"
    assert len(res.attempts) == 1


def test_retries_then_succeeds_with_backoff(fake_tool, router_factory):
    t = fake_tool("a", fail_times=2)
    delays = []
    router = router_factory(t, max_attempts=3, base_delay=1.0, sleep=delays.append)
    res = router.run("web_search", "q")
    assert res.tool_used == "a"
    assert [a.ok for a in res.attempts] == [False, False, True]
    # exponential: ~1s then ~2s (plus up to 10% jitter)
    assert 1.0 <= delays[0] <= 1.1 and 2.0 <= delays[1] <= 2.2


def test_falls_back_after_retries_exhausted(fake_tool, router_factory):
    a = fake_tool("a", priority=10, fail_times=99)
    b = fake_tool("b", priority=20)
    res = router_factory(a, b, max_attempts=3).run("web_search", "q")
    assert res.tool_used == "b"
    assert [x.tool for x in res.attempts] == ["a", "a", "a", "b"]


def test_non_retryable_error_skips_straight_to_fallback(fake_tool, router_factory):
    a = fake_tool("a", fail_times=99, retryable=False)
    b = fake_tool("b", priority=20)
    res = router_factory(a, b, max_attempts=3).run("web_search", "q")
    assert len(a.calls) == 1 and res.tool_used == "b"


def test_empty_results_fall_back_without_retry(fake_tool, router_factory):
    a = fake_tool("a", results=[])
    b = fake_tool("b", priority=20)
    res = router_factory(a, b).run("web_search", "q")
    assert len(a.calls) == 1 and res.tool_used == "b"
    assert res.attempts[0].error == "no results"


def test_unavailable_tool_is_skipped(fake_tool, router_factory):
    a = fake_tool("a", available=False)
    b = fake_tool("b", priority=20)
    res = router_factory(a, b).run("web_search", "q")
    assert a.calls == [] and res.tool_used == "b"


def test_timeout_counts_as_failure(fake_tool, router_factory):
    slow = fake_tool("slow", delay=0.5, timeout=0.05)
    fast = fake_tool("fast", priority=20)
    res = router_factory(slow, fast, max_attempts=1).run("web_search", "q")
    assert res.tool_used == "fast"
    assert "timed out" in res.attempts[0].error


def test_all_tools_fail(fake_tool, router_factory):
    res = router_factory(fake_tool("a", fail_times=99), max_attempts=2).run("web_search", "q")
    assert not res.ok and res.results == [] and len(res.attempts) == 2


def test_unknown_category_returns_empty(router_factory):
    res = router_factory().run("nope", "q")
    assert not res.ok and res.attempts == []


def test_prefer_moves_tool_first(fake_tool, router_factory):
    a, b = fake_tool("a", priority=10), fake_tool("b", priority=20)
    assert router_factory(a, b).run("web_search", "q", prefer="b").tool_used == "b"


def test_arun_runs_concurrently(fake_tool, router_factory):
    tools = [fake_tool(f"t{i}", category=f"c{i}", delay=0.3) for i in range(4)]
    router = router_factory(*tools)

    async def go():
        return await asyncio.gather(*(router.arun(f"c{i}", "q") for i in range(4)))

    start = time.monotonic()
    results = asyncio.run(go())
    assert all(r.ok for r in results)
    assert time.monotonic() - start < 0.9  # 4 x 0.3s sequentially would be 1.2s
