import importlib.util
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_DIR = BASE_DIR / "prompt_examples"
RAG_DIR = BASE_DIR / "rag_minimal"
AGENT_DIR = BASE_DIR / "agent_minimal"
SAFETY_DIR = BASE_DIR / "safety_logging"

for module_dir in [str(AGENT_DIR), str(RAG_DIR), str(SAFETY_DIR)]:
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

from planner import run_agent  # noqa: E402
from rag_engine import MinimalRAG  # noqa: E402
from safety import check_prompt_safety, check_tool_allowed  # noqa: E402


def _load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prompt_client = _load_module_from_path("prompt_ollama_client", PROMPT_DIR / "ollama_client.py")
prompt_defs = _load_module_from_path("prompt_defs", PROMPT_DIR / "prompts.py")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

rag = MinimalRAG(data_dir=str(RAG_DIR / "data"))
rag.build()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


@app.route("/api/portal/health", methods=["GET"])
def health():
    return jsonify(
        {
            "success": True,
            "services": ["prompt_ab", "rag", "agent", "safety"],
            "model": OLLAMA_MODEL,
            "ollamaBaseUrl": OLLAMA_BASE_URL,
            "ragChunks": len(rag.chunks),
        }
    )


@app.route("/api/portal/prompt_ab", methods=["POST"])
def prompt_ab():
    data = request.json or {}
    task = (data.get("task") or "").strip()
    if not task:
        return jsonify({"success": False, "errorCode": "ERR_EMPTY_TASK", "message": "task 不能为空"}), 400
    user_prompt = prompt_defs.USER_TEMPLATE.format(task=task)
    result_a = prompt_client.chat_json(prompt_defs.SYSTEM_PROMPT_A, user_prompt)
    result_b = prompt_client.chat_json(prompt_defs.SYSTEM_PROMPT_B, user_prompt)
    return jsonify({"success": True, "result": {"task": task, "A": result_a, "B": result_b}})


@app.route("/api/portal/rag_ask", methods=["POST"])
def rag_ask():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"success": False, "errorCode": "ERR_EMPTY_QUERY", "message": "query 不能为空"}), 400
    top_k = int(data.get("top_k", 3))
    result = rag.answer(query, top_k=top_k)
    return jsonify({"success": True, "result": result})


@app.route("/api/portal/agent_chat", methods=["POST"])
def agent_chat():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"success": False, "errorCode": "ERR_EMPTY_QUERY", "message": "query 不能为空"}), 400
    context = data.get("context") or {}
    result = run_agent(query, context)
    return jsonify({"success": True, "result": result})


@app.route("/api/portal/safety_check", methods=["POST"])
def safety_check():
    data = request.json or {}
    text = data.get("text", "")
    tool_name = data.get("tool", "")
    prompt_ok, prompt_code = check_prompt_safety(text)
    tool_ok, tool_code = check_tool_allowed(tool_name) if tool_name else (True, "SKIP")
    return jsonify(
        {
            "success": True,
            "result": {
                "promptSafe": prompt_ok,
                "promptCode": prompt_code,
                "toolAllowed": tool_ok,
                "toolCode": tool_code,
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
