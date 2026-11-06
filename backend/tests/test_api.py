import fakeredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue

import app as app_module
import jobs
import workflows.research_workflow as wf

FAKE_STATE = {
    "report": "# R [1]",
    "subtasks": [{"id": 1, "goal": "g", "category": "web_search", "input": "q"}],
    "sources": [{"n": 1, "title": "t", "url": "https://x", "snippet": "s", "tool": "wikipedia"}],
    "results": [{"subtask": {"id": 1}, "route": {"category": "web_search", "tool_used": "wikipedia", "attempts": []}}],
}


@pytest.fixture
def client(monkeypatch):
    redis = fakeredis.FakeRedis()
    # is_async=False runs the job immediately in-process, like a worker would.
    queue = Queue("research", connection=redis, is_async=False)
    monkeypatch.setattr(jobs, "get_redis", lambda: redis)
    monkeypatch.setattr(jobs, "get_queue", lambda: queue)

    def fake_run(query, on_event=None, **_):
        if on_event:
            on_event("planner", {"subtasks": FAKE_STATE["subtasks"]})
            on_event("execute_subtask", {})
            on_event("synthesizer", {})
        return FAKE_STATE

    monkeypatch.setattr(wf, "run_research", fake_run)
    monkeypatch.setattr(app_module, "run_research", fake_run)
    return app_module.app.test_client()


def test_missing_query(client):
    assert client.post("/api/research", json={}).status_code == 400


def test_enqueue_then_poll(client):
    r = client.post("/api/research", json={"query": "quantum"})
    assert r.status_code == 202
    job_id = r.get_json()["job_id"]

    s = client.get(f"/api/research/{job_id}").get_json()
    assert s["status"] == "finished" and s["stage"] == "Done"
    assert s["progress"] == {"total": 1, "done": 1}
    assert s["result"]["report"] == "# R [1]"
    assert s["result"]["tool_log"][0]["tool_used"] == "wikipedia"


def test_unknown_job(client):
    assert client.get("/api/research/does-not-exist").status_code == 404


def test_falls_back_to_inline_when_redis_down(client, monkeypatch):
    def down(*_):
        raise RedisConnectionError("refused")

    monkeypatch.setattr(jobs, "enqueue_research", down)
    r = client.post("/api/research", json={"query": "quantum"})
    assert r.status_code == 200 and r.get_json()["report"] == "# R [1]"


def test_sync_flag_skips_queue(client):
    r = client.post("/api/research?sync=1", json={"query": "quantum"})
    assert r.status_code == 200 and r.get_json()["sources"][0]["url"] == "https://x"


def test_failed_job_reports_error(client, monkeypatch):
    def boom(query, on_event=None, **_):
        raise RuntimeError("LLM quota exceeded")

    monkeypatch.setattr(wf, "run_research", boom)
    job_id = client.post("/api/research", json={"query": "q"}).get_json()["job_id"]
    s = client.get(f"/api/research/{job_id}").get_json()
    assert s["status"] == "failed" and "LLM quota exceeded" in s["error"]


def test_tools_endpoint(client):
    data = client.get("/api/tools").get_json()
    assert data["count"] >= 10
