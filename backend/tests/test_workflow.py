import json
import time

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from tools import Source
from workflows.research_workflow import collect_sources, parse_plan, run_research

ALLOWED = ["web_search", "academic_search", "code_execution"]


def plan(*subtasks):
    return json.dumps({"subtasks": [
        {"id": i + 1, "goal": f"goal {i + 1}", "category": c, "input": inp} for i, (c, inp) in enumerate(subtasks)
    ]})


# ---------------------------------------------------------------- planner parsing

def test_parse_plan_valid():
    out = parse_plan(plan(("web_search", "a"), ("academic_search", "b")), "q", ALLOWED)
    assert [s["category"] for s in out] == ["web_search", "academic_search"]


def test_parse_plan_handles_code_fences():
    out = parse_plan("```json\n" + plan(("web_search", "a")) + "\n```", "q", ALLOWED)
    assert out[0]["input"] == "a"


def test_parse_plan_drops_unknown_categories_and_caps_count():
    text = plan(("teleport", "x"), *[("web_search", str(i)) for i in range(10)])
    out = parse_plan(text, "q", ALLOWED, max_subtasks=3)
    assert len(out) == 3 and all(s["category"] == "web_search" for s in out)
    assert [s["id"] for s in out] == [1, 2, 3]


def test_parse_plan_falls_back_on_garbage():
    out = parse_plan("sorry, I can't do JSON", "quantum computing", ALLOWED)
    assert {s["category"] for s in out} == {"web_search", "academic_search"}
    assert all(s["input"] == "quantum computing" for s in out)


# ---------------------------------------------------------------- full graph

def test_subtasks_run_concurrently_and_report_cites_sources(fake_tool, router_factory):
    web = fake_tool("web", "web_search", delay=0.4,
                    results=[Source(title="Web page", url="https://web.example/a", snippet="web fact")])
    papers = fake_tool("papers", "academic_search", delay=0.4,
                       results=[Source(title="A Paper", url="https://arxiv.org/abs/1", snippet="paper fact",
                                       metadata={"authors": "Smith", "year": 2024})])
    calc = fake_tool("calc", "code_execution", delay=0.4, results=[Source(title="Python execution result", snippet="42")])
    router = router_factory(web, papers, calc)
    llm = FakeListChatModel(responses=[
        plan(("web_search", "overview"), ("academic_search", "papers"), ("code_execution", "print(42)")),
        "# Report\n\n## Findings\n\nWeb says X [1]. Papers say Y [2]. The answer is 42 [3].",
    ])

    events = []
    start = time.monotonic()
    state = run_research("test query", llm=llm, router=router, on_event=lambda n, u: events.append(n))
    elapsed = time.monotonic() - start

    assert elapsed < 1.0, f"subtasks ran sequentially ({elapsed:.2f}s for 3 x 0.4s)"
    assert len(state["results"]) == 3
    assert events.count("execute_subtask") == 3 and events[0] == "planner" and events[-1] == "synthesizer"
    report = state["report"]
    assert "## References" in report
    assert "[1] Web page. <https://web.example/a> _(via web)_" in report
    assert "[2] A Paper. Smith (2024). <https://arxiv.org/abs/1> _(via papers)_" in report
    assert "## How this report was researched" in report


def test_failed_tool_falls_back_inside_workflow(fake_tool, router_factory):
    broken = fake_tool("broken", "web_search", priority=10, fail_times=99)
    backup = fake_tool("backup", "web_search", priority=20)
    llm = FakeListChatModel(responses=[plan(("web_search", "x")), "Report [1]"])
    state = run_research("q", llm=llm, router=router_factory(broken, backup, max_attempts=2))
    assert state["results"][0]["route"]["tool_used"] == "backup"
    assert "broken ✗ → broken ✗ → backup" in state["report"]


def test_llm_failure_still_returns_sources(fake_tool, router_factory):
    class BrokenLLM:
        def invoke(self, *_):
            raise RuntimeError("LLM down")

    router = router_factory(fake_tool("w", "web_search"), fake_tool("p", "academic_search"))
    state = run_research("q", llm=BrokenLLM(), router=router)
    # Planner falls back to the default plan; synthesizer still lists sources.
    assert len(state["results"]) == 2
    assert "could not be written" in state["report"] and "## References" in state["report"]


def test_collect_sources_dedupes_by_url():
    r = lambda sid, url: {"subtask": {"id": sid}, "route": {"results": [{"title": "t", "url": url, "snippet": "", "tool": "x"}]}}
    out = collect_sources([r(2, "https://a"), r(1, "https://a"), r(3, "https://b")])
    assert [s["url"] for s in out] == ["https://a", "https://b"]
    assert [s["n"] for s in out] == [1, 2]
