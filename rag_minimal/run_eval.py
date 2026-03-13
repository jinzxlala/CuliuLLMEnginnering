import json
import os

from rag_engine import MinimalRAG


def main() -> None:
    rag = MinimalRAG()
    rag.build()
    fixture = os.path.join("evals", "fixtures", "easy.jsonl")
    total, passed = 0, 0
    rows = []
    with open(fixture, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            total += 1
            result = rag.answer(item["query"], top_k=3, use_llm=False)
            ok = item["must_include"] in result["answer"]
            passed += int(ok)
            rows.append(
                {
                    "query": item["query"],
                    "pass": ok,
                    "answer": result["answer"],
                    "citations": result["citations"],
                }
            )

    os.makedirs("reports", exist_ok=True)
    with open(os.path.join("reports", "eval_report.json"), "w", encoding="utf-8") as f:
        json.dump({"total": total, "passed": passed, "rows": rows}, f, ensure_ascii=False, indent=2)
    print(f"RAG eval: {passed}/{total}")


if __name__ == "__main__":
    main()
