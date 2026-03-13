from flask import Flask, jsonify, request

from rag_engine import MinimalRAG

app = Flask(__name__)
rag = MinimalRAG()
rag.build()


@app.route("/api/rag/health", methods=["GET"])
def health():
    return jsonify({"success": True, "chunks": len(rag.chunks)})


@app.route("/api/rag/ask", methods=["POST"])
def ask():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"success": False, "errorCode": "ERR_EMPTY_QUERY", "message": "query 不能为空"}), 400
    top_k = int(data.get("top_k", 3))
    result = rag.answer(query, top_k=top_k)
    return jsonify({"success": True, "result": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
