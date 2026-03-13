import json
import os
import time
from typing import Dict

LOG_DIR = "logs"
REPORT_DIR = "reports"
LOG_FILE = os.path.join(LOG_DIR, "runtime_log.jsonl")
METRICS_FILE = os.path.join(REPORT_DIR, "runtime_metrics.json")


def _ensure_dirs() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)


def append_log(event: Dict) -> None:
    _ensure_dirs()
    event["ts"] = time.time()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def update_metrics(success: bool) -> Dict:
    _ensure_dirs()
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    else:
        metrics = {"totalCalls": 0, "totalFailures": 0, "failureRate": 0.0, "updatedAt": 0}
    metrics["totalCalls"] += 1
    if not success:
        metrics["totalFailures"] += 1
    metrics["failureRate"] = metrics["totalFailures"] / metrics["totalCalls"]
    metrics["updatedAt"] = time.time()
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    return metrics
