from flask import Flask, jsonify, request

from logger import append_log, update_metrics
from safety import check_prompt_safety, check_tool_allowed

app = Flask(__name__)


@app.route("/api/safety/health", methods=["GET"])
def health():
    return jsonify({"success": True})


@app.route("/api/safety/guard_prompt", methods=["POST"])
def guard_prompt():
    data = request.json or {}
    text = data.get("text", "")
    ok, code = check_prompt_safety(text)
    append_log({"type": "guard_prompt", "ok": ok, "code": code, "inputLen": len(text)})
    metrics = update_metrics(ok)
    if not ok:
        return jsonify({"success": False, "errorCode": code, "metrics": metrics}), 400
    return jsonify({"success": True, "code": code, "metrics": metrics})


@app.route("/api/safety/guard_tool", methods=["POST"])
def guard_tool():
    data = request.json or {}
    tool = data.get("tool", "")
    ok, code = check_tool_allowed(tool)
    append_log({"type": "guard_tool", "ok": ok, "code": code, "tool": tool})
    metrics = update_metrics(ok)
    if not ok:
        return jsonify({"success": False, "errorCode": code, "metrics": metrics}), 400
    return jsonify({"success": True, "code": code, "metrics": metrics})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5053, debug=True)
