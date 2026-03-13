from typing import Dict, List

from ollama_client import chat
from tools import evaluate_move, get_rules


SYSTEM_PROMPT = (
    "你是课程中的最小 Agent。优先基于工具结果回答，"
    "输出简洁、可验证，不编造规则。"
)


def _synthesize_by_llm(user_query: str, tool_name: str, tool_result: Dict, trace: List[Dict]) -> Dict:
    prompt = (
        f"用户问题: {user_query}\n"
        f"工具名: {tool_name}\n"
        f"工具结果: {tool_result}\n\n"
        "请基于工具结果给出面向学生的最终回答，"
        "必须解释结论，不得编造工具结果中不存在的信息。"
    )
    answer = chat(SYSTEM_PROMPT, prompt)
    trace.append({"step": "llm_synthesis", "tool": tool_name})
    return {"answer": answer, "trace": trace}


def run_agent(user_query: str, context: Dict) -> Dict:
    trace: List[Dict] = []
    lower = user_query.lower()

    if "规则" in user_query or "rule" in lower:
        trace.append({"step": "route", "decision": "get_rules"})
        rules = get_rules()
        trace.append({"step": "tool_call", "tool": "get_rules", "result": {"rules": rules}})
        return _synthesize_by_llm(user_query, "get_rules", {"rules": rules}, trace)

    if any(k in user_query for k in ["合法", "落子", "校验", "evaluate"]):
        trace.append({"step": "route", "decision": "evaluate_move"})
        grid = context.get("grid") or [[None for _ in range(5)] for _ in range(5)]
        row = int(context.get("row", 0))
        col = int(context.get("col", 0))
        value = str(context.get("value", "X"))
        result = evaluate_move(grid, row, col, value)
        trace.append({"step": "tool_call", "tool": "evaluate_move", "result": result})
        return _synthesize_by_llm(user_query, "evaluate_move", result, trace)

    trace.append({"step": "route", "decision": "llm_fallback"})
    prompt = f"用户问题: {user_query}\n已知规则摘要: {get_rules()}"
    answer = chat(SYSTEM_PROMPT, prompt)
    return {"answer": answer, "trace": trace}
