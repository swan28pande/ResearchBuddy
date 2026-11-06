from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import threading
import sys
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from rq.job import Job
import jobs
from tools import build_default_registry
from workflows.research_workflow import run_research

app = Flask(__name__)
CORS(app)
logger = logging.getLogger(__name__)


@app.route("/api/research", methods=["POST"])
def research():
    """Queue a research job (202 + job_id). Runs inline if ?sync=1 or Redis is unreachable."""
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400

    if request.args.get("sync") != "1":
        try:
            job = jobs.enqueue_research(query)
            return jsonify({"job_id": job.id, "status_url": f"/api/research/{job.id}"}), 202
        except RedisError as e:
            logger.warning("Redis unavailable (%s); running research inline", e)

    return jsonify(jobs.serialize_state(run_research(query)))


@app.route("/api/research/<job_id>", methods=["GET"])
def research_status(job_id):
    try:
        job = Job.fetch(job_id, connection=jobs.get_redis())
    except NoSuchJobError:
        return jsonify({"error": "Unknown job"}), 404
    except RedisError:
        return jsonify({"error": "Queue unavailable"}), 503

    status = job.get_status()
    status = getattr(status, "value", status)
    body = {"job_id": job.id, "status": status, "stage": job.meta.get("stage"),
            "progress": job.meta.get("progress")}
    if status == "finished":
        body["result"] = job.return_value()
    elif status == "failed":
        result = job.latest_result()
        exc = (result.exc_string or "") if result else ""
        body["error"] = exc.strip().splitlines()[-1] if exc.strip() else "Job failed"
    return jsonify(body)


@app.route("/api/tools", methods=["GET"])
def list_tools():
    registry = build_default_registry()
    return jsonify({"count": len(registry), "tools": [t.info() for t in registry.all()]})

@app.route("/sum", methods=["POST"])
def add():
    data = request.json
    return jsonify({"sum": data["a"] + data["b"]})

@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"msg": "Hello, Chainsaw!"})

if __name__ == "__main__":
    # Load-testing helper; only needed when running this file directly.
    sys.path.append("../chainsaw")
    from chainsaw import Chainsaw

    chainsaw = Chainsaw(app, base_url="http://127.0.0.1:8000", auto_start=False, concurrency=10, duration=15)

    # Register POST schemas
    chainsaw.register_schema("/sum", {"a": "int", "b": "int"})
    chainsaw.register_schema("/api/research", {"query": "str"})

    # Print routes with body
    chainsaw.print_routes()

    # Run Chainsaw in background
    t = threading.Thread(target=chainsaw.run, daemon=True)
    t.start()

    # Start Flask
    app.run(host="0.0.0.0", port=8000, debug=True)
