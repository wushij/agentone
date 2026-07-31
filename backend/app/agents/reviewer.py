"""app/agents/reviewer.py — Reviewer Agent

§3.3 反思闭环：输出结构化 {verdict, feedback, score}，
verdict 驱动条件边 retry（重执行工具）/ replan（重新规划）/ approved。
Prompt 拼装已收口至 ContextBuilder（§6.1）。
"""

from __future__ import annotations

import json
import re

from app.core.context.state import AgentState
from app.llm.factory import create_chat_model

MAX_REFLECTIONS = 2  # 防死循环

_STRUCTURED_SUFFIX = (
    "\n\n请在回答末尾追加一行 JSON（不要放进代码块），格式："
    '{"verdict": "approved|retry|replan", "score": 0.0到1.0}\n'
    "verdict 判定标准：结果正确且完整=approved；工具结果有误/不完整需重新执行=retry；"
    "方向就错了需要重新规划=replan。"
)


def parse_review(content: str) -> dict:
    """解析 reviewer 输出为结构化结果；解析失败按文本语义兜底。"""
    verdict, score = "approved", 1.0
    match = re.search(r'\{[^{}]*"verdict"[^{}]*\}', content)
    if match:
        try:
            parsed = json.loads(match.group(0))
            v = str(parsed.get("verdict") or "").lower()
            if v in ("approved", "retry", "replan"):
                verdict = v
            score = float(parsed.get("score", 1.0))
        except Exception:
            pass
    elif "APPROVED" not in content.upper():
        # 无 JSON 且未明示通过：保守视为通过（旧行为兼容），但降低置信度
        score = 0.6
    feedback = re.sub(r'\{[^{}]*"verdict"[^{}]*\}', "", content).strip()
    return {"verdict": verdict, "feedback": feedback, "score": max(0.0, min(1.0, score))}


async def reviewer_node(state: AgentState) -> dict:
    model_id = (state.get("metadata") or {}).get("model_id")
    llm = create_chat_model(model=model_id)

    from app.runtime.context.builder import get_context_builder

    messages, _context_state = get_context_builder().build("reviewer", dict(state))
    # 追加结构化输出指令（Judge 格式）
    if messages and hasattr(messages[-1], "content"):
        messages[-1].content = str(messages[-1].content) + _STRUCTURED_SUFFIX

    response = await llm.ainvoke(messages)
    review_content = response.content if isinstance(response.content, str) else str(response.content)
    review = parse_review(review_content)

    reflections = int((state.get("metadata") or {}).get("reflections") or 0)
    if review["verdict"] != "approved" and reflections >= MAX_REFLECTIONS:
        # 反思次数用尽：强制收敛，带着 feedback 去总结
        review["verdict"] = "approved"

    return {
        "current_node": "reviewer",
        "metadata": {
            "review": review["feedback"],
            "review_verdict": review["verdict"],
            "review_score": review["score"],
            "reflections": reflections + (0 if review["verdict"] == "approved" else 1),
        },
    }


def route_after_reviewer(state: AgentState) -> str:
    """反思回边（§3.3）：approved → END；retry → tool；replan → planner。"""
    meta = state.get("metadata") or {}
    verdict = str(meta.get("review_verdict") or "approved")
    if verdict == "retry" and state.get("tool_name"):
        return "tool"
    if verdict == "replan":
        return "planner"
    return "end"
