from flask import Flask, jsonify, request

from planner import run_agent

app = Flask(__name__)


@app.route("/api/agent/health", methods=["GET"])
def health():
    return jsonify({"success": True, "service": "agent_minimal"})


@app.route("/api/agent/chat", methods=["POST"])
def chat():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"success": False, "errorCode": "ERR_EMPTY_QUERY", "message": "query 不能为空"}), 400
    context = data.get("context") or {}
    result = run_agent(query, context)
    return jsonify({"success": True, "result": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5052, debug=True)
