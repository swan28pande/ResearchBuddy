from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from workflows.research_workflow import build_and_run_workflow

app = Flask(__name__)
CORS(app)  # Allow all origins for development; restrict in production

PDF_DIR = os.path.abspath(os.path.dirname(__file__))

@app.route("/api/research", methods=["POST"])
def research():
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    report = build_and_run_workflow(query)
    return jsonify({"report": report})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
