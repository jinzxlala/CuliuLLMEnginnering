from typing import Tuple

BLOCK_PATTERNS = [
    "ignore previous instructions",
    "system prompt",
    "泄露",
    "越权",
]

ALLOWED_TOOLS = {"get_rules", "evaluate_move", "list_legal_moves", "explain_scoring"}


def check_prompt_safety(text: str, max_len: int = 1200) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "ERR_EMPTY_INPUT"
    if len(text) > max_len:
        return False, "ERR_INPUT_TOO_LONG"
    lower = text.lower()
    for p in BLOCK_PATTERNS:
        if p in lower:
            return False, "ERR_PROMPT_INJECTION"
    return True, "OK"


def check_tool_allowed(tool_name: str) -> Tuple[bool, str]:
    if tool_name not in ALLOWED_TOOLS:
        return False, "ERR_TOOL_NOT_ALLOWED"
    return True, "OK"
