"""app/knowledge/transform/query_transform.py — 检索前查询变换（§8.2）

- Rewrite：结合对话历史把口语化/指代性问题改写为独立完整查询
- MultiQuery：一个问题扩展为多个不同角度查询，并行检索后去重合并

均为"最划算的检索质量投资之一"；LLM 不可用时回退原查询，绝不阻断检索。
按知识库配置 queryTransform 启用（["rewrite","multi_query"]）。
"""

from __future__ import annotations

import re

from app.utils.logger import logger


async def rewrite_query(query: str, history: list | None = None) -> str:
    """把口语化/指代性问题改写为独立完整查询。失败回退原查询。"""
    if not query.strip():
        return query
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from app.llm.factory import create_chat_model

        ctx = ""
        if history:
            recent = history[-4:]
            lines = []
            for m in recent:
                role = getattr(m, "type", None) or "user"
                content = str(getattr(m, "content", "") or "")[:200]
                lines.append(f"{role}: {content}")
            ctx = "对话历史：\n" + "\n".join(lines) + "\n\n"

        llm = create_chat_model()
        response = await llm.ainvoke(
            [
                SystemMessage(
                    content="把用户问题改写为一个独立、完整、适合知识库检索的查询。消解指代（它/这个/上面）。只输出改写后的查询，不要解释。"
                ),
                HumanMessage(content=f"{ctx}原始问题：{query}"),
            ]
        )
        rewritten = (response.content if isinstance(response.content, str) else str(response.content)).strip()
        return rewritten or query
    except Exception as exc:
        logger.warning(f"[QueryTransform] rewrite 失败，回退原查询: {exc}")
        return query


async def multi_query(query: str, n: int = 3) -> list[str]:
    """把问题扩展为 n 个不同角度的查询（含原查询）。失败回退 [原查询]。"""
    if not query.strip():
        return [query]
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from app.llm.factory import create_chat_model

        llm = create_chat_model()
        response = await llm.ainvoke(
            [
                SystemMessage(
                    content=f"针对用户问题，生成 {n} 个不同角度/措辞的检索查询，覆盖同义表达与相关概念。每行一个查询，不要编号、不要解释。"
                ),
                HumanMessage(content=query),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        variants = [re.sub(r"^\s*[\d.\-、）)]+\s*", "", line).strip() for line in text.splitlines()]
        variants = [v for v in variants if v]
        merged = list(dict.fromkeys([query] + variants))
        return merged[: n + 1]
    except Exception as exc:
        logger.warning(f"[QueryTransform] multi_query 失败，回退原查询: {exc}")
        return [query]


async def transform_query(
    query: str,
    modes: list[str] | None = None,
    history: list | None = None,
) -> list[str]:
    """按配置执行变换，返回待检索的查询列表（至少含原查询）。"""
    modes = modes or []
    current = query
    if "rewrite" in modes:
        current = await rewrite_query(query, history)
    if "multi_query" in modes:
        return await multi_query(current)
    return [current]
