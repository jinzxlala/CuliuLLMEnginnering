import os

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_THINKING = os.getenv("OLLAMA_THINKING", "0").lower() in ("1", "true", "yes", "on")


def _maybe_disable_thinking_prompt(text: str) -> str:
    if OLLAMA_THINKING:
        return text
    return "/no_think\n" + text


def chat(system_prompt: str, user_prompt: str, timeout: int = 120) -> str:
    try:
        user_prompt = _maybe_disable_thinking_prompt(user_prompt)
        payload = {
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
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=timeout)
        if resp.status_code == 404:
            payload_generate = {
                "model": OLLAMA_MODEL,
                "stream": False,
                "think": OLLAMA_THINKING,
                "thinking": OLLAMA_THINKING,
                "prompt": f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
                "options": {"temperature": 0.2},
            }
            resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload_generate, timeout=timeout)
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
                return (
                    resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        return "模型当前不可达，已返回离线降级答案。"
