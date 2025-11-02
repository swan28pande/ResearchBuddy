from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import sys
sys.path.append("../chainsaw")
from chainsaw import Chainsaw
from workflows.research_workflow import build_and_run_workflow

app = Flask(__name__)
CORS(app)

@app.route("/api/research", methods=["POST"])
def research():
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    report = build_and_run_workflow(query)
    return jsonify({"report": report})

@app.route("/sum", methods=["POST"])
def add():
    data = request.json
    return jsonify({"sum": data["a"] + data["b"]})

@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"msg": "Hello, Chainsaw!"})

if __name__ == "__main__":
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
