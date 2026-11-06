"""Redis-backed task queue (RQ) for research jobs.

The Flask request only enqueues a job and returns its id, so a slow research run
never blocks a web worker. One or more `rq worker research` processes pick jobs
off the queue. Progress is written to job.meta, which the status endpoint reads.

Run a worker:  rq worker research --url $REDIS_URL
(on macOS add  --worker-class rq.worker.SimpleWorker  to avoid fork issues)
"""

import os
from typing import Any, Dict

from redis import Redis
from rq import Queue, Retry, get_current_job

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = "research"
JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "600"))

_redis = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(REDIS_URL, socket_connect_timeout=2)
    return _redis


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis())


def enqueue_research(query: str, queue: Queue = None):
    queue = queue or get_queue()
    return queue.enqueue(
        run_research_job, query,
        job_timeout=JOB_TIMEOUT,
        result_ttl=3600, failure_ttl=24 * 3600,
        # Job-level retry for crashes the tool router can't absorb (e.g. LLM outage).
        retry=Retry(max=1, interval=30),
        meta={"stage": "Queued"},
    )


def serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "report": state.get("report", ""),
        "subtasks": state.get("subtasks", []),
        "sources": state.get("sources", []),
        "tool_log": [
            {
                "subtask_id": r["subtask"]["id"],
                "category": r["route"]["category"],
                "tool_used": r["route"]["tool_used"],
                "attempts": r["route"]["attempts"],
            }
            for r in state.get("results", [])
        ],
    }


def run_research_job(query: str) -> Dict[str, Any]:
    from workflows.research_workflow import run_research

    job = get_current_job()
    progress = {"total": 0, "done": 0}

    def set_stage(text: str):
        if job:
            job.meta["stage"] = text
            job.meta["progress"] = dict(progress)
            job.save_meta()

    def on_event(node: str, update: Dict[str, Any]):
        if node == "planner":
            progress["total"] = len(update.get("subtasks", []))
            set_stage(f"Running {progress['total']} subtasks in parallel")
        elif node == "execute_subtask":
            progress["done"] += 1
            if progress["done"] >= progress["total"]:
                set_stage("Writing report")
            else:
                set_stage(f"Running subtasks ({progress['done']}/{progress['total']} done)")
        elif node == "synthesizer":
            set_stage("Done")

    set_stage("Planning subtasks")
    return serialize_state(run_research(query, on_event=on_event))
