import json
import os
from typing import Any, Dict

import requests


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_THINKING = os.getenv("OLLAMA_THINKING", "0").lower() in ("1", "true", "yes", "on")


def _maybe_disable_thinking_prompt(text: str) -> str:
    if OLLAMA_THINKING:
        return text
    # qwen 系列通常支持 no_think 指令；不支持时也不会破坏主语义
    return "/no_think\n" + text


def chat_json(system_prompt: str, user_prompt: str, timeout: int = 120) -> Dict[str, Any]:
    try:
        user_prompt = _maybe_disable_thinking_prompt(user_prompt)
        payload_chat = {
            "model": OLLAMA_MODEL,
            "stream": False,
            "think": OLLAMA_THINKING,
            "thinking": OLLAMA_THINKING,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload_chat, timeout=timeout)
        if resp.status_code == 404:
            payload_gen = {
                "model": OLLAMA_MODEL,
                "stream": False,
                "think": OLLAMA_THINKING,
                "thinking": OLLAMA_THINKING,
                "prompt": f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
                "options": {"temperature": 0.2},
            }
            resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload_gen, timeout=timeout)
            if resp.status_code == 404:
                payload_openai = {
                    "model": OLLAMA_MODEL,
                    "temperature": 0.2,
                    "think": OLLAMA_THINKING,
                    "thinking": OLLAMA_THINKING,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                }
                resp = requests.post(
                    f"{OLLAMA_BASE_URL}/v1/chat/completions", json=payload_openai, timeout=timeout
                )
                resp.raise_for_status()
                text = (
                    resp.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
            else:
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
        else:
            resp.raise_for_status()
            text = resp.json().get("message", {}).get("content", "").strip()
        return _safe_json_parse(text)
    except Exception:
        # 本地模型不可达时，返回可评测的降级结果，保证课堂流程可继续
        return {
            "task_type": "fallback",
            "answer": "模型当前不可用，已切换为离线占位输出。请检查 OLLAMA_BASE_URL 和模型名。",
            "confidence": 0.0,
            "citations": ["offline-fallback"],
        }


def _safe_json_parse(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise ValueError(f"模型输出不是合法 JSON: {text[:200]}")
