"""backend/app/runtime/evals/judge.py — LLM-as-Judge（§13.1）

对 RAG 回答做三元组评分（faithfulness / answer_relevancy / context_precision），
1-5 分。LLM 不可用时回退启发式（词法重合），保证 CI 可运行。
"""

from __future__ import annotations

import json
import re


def _lexical(a: str, b: str) -> float:
    sa, sb = set(a.lower().split()), set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


async def judge_rag(query: str, context: str, answer: str) -> dict[str, float]:
    """返回 {faithfulness, answerRelevancy, contextPrecision}，均为 1~5。"""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from app.llm.factory import create_chat_model

        llm = create_chat_model()
        response = await llm.ainvoke(
            [
                SystemMessage(
                    content=(
                        "你是严格的 RAG 质量评审。基于给定问题/参考资料/回答，输出 JSON："
                        '{"faithfulness":1-5,"answerRelevancy":1-5,"contextPrecision":1-5}。'
                        "faithfulness=回答是否忠于资料无幻觉；answerRelevancy=回答是否切题；"
                        "contextPrecision=资料是否与问题相关。只输出 JSON。"
                    )
                ),
                HumanMessage(content=f"问题：{query}\n\n参考资料：{context}\n\n回答：{answer}"),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        match = re.search(r"\{[^{}]*\}", text)
        if match:
            data = json.loads(match.group(0))
            return {
                "faithfulness": float(data.get("faithfulness", 3)),
                "answerRelevancy": float(data.get("answerRelevancy", 3)),
                "contextPrecision": float(data.get("contextPrecision", 3)),
            }
    except Exception:
        pass
    # 回退启发式：把词法重合映射到 1~5
    faith = 1 + 4 * _lexical(answer, context)
    rel = 1 + 4 * _lexical(answer, query)
    prec = 1 + 4 * _lexical(context, query)
    return {"faithfulness": round(faith, 2), "answerRelevancy": round(rel, 2), "contextPrecision": round(prec, 2)}
