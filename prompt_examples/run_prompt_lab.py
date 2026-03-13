import argparse
import json
import os
import time
from typing import Dict, List

from ollama_client import chat_json
from prompts import SYSTEM_PROMPT_A, SYSTEM_PROMPT_B, USER_TEMPLATE


def eval_one(task: str) -> Dict:
    user_prompt = USER_TEMPLATE.format(task=task)
    result_a = chat_json(SYSTEM_PROMPT_A, user_prompt)
    result_b = chat_json(SYSTEM_PROMPT_B, user_prompt)
    return {"task": task, "A": result_a, "B": result_b, "timestamp": time.time()}


def eval_batch(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rows.append(eval_one(item["task"]))
    return rows


def save_report(rows: List[Dict]) -> str:
    os.makedirs("reports", exist_ok=True)
    output_path = os.path.join("reports", "prompt_ab_results.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="")
    parser.add_argument("--batch", type=str, default="")
    args = parser.parse_args()

    if not args.task and not args.batch:
        raise ValueError("请提供 --task 或 --batch")

    if args.task:
        result = eval_one(args.task)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    rows = eval_batch(args.batch)
    output = save_report(rows)
    print(f"批量评测完成: {output}, 共 {len(rows)} 条")


if __name__ == "__main__":
    main()
