"""app/services/conversation/conversation_title_service.py — 会话标题自动精炼与总结服务"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.factory import create_chat_model

_TITLE_PROMPT = (
    "你是专业的会话标题提炼专家。请根据用户的对话内容，总结归纳出一个高度概括、专业简洁的中文标题。"
    "严格要求：4-12个字，提炼出核心主题概念（例如：'Python 乘法计算'、'广州天气咨询'、'AI系统架构解析'）。"
    "绝不能原封不动复制用户的长句子，不要加引号或句号，只输出标题本身。"
)


def _clean_title(text: str) -> str:
    if not text:
        return "新对话"
    text = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"[\*\`\_]+", "", text)
    return " ".join(text.strip().split())


def _summarize_rule_title(user_message: str) -> str:
    """当大模型未响应或超时时的智能主题归纳规则"""
    msg = user_message.strip()
    if not msg:
        return "新对话"

    # 关键词意图归纳规则
    if any(w in msg for w in ("天气", "气温", "下雨", "预报")):
        city = re.search(r"([\u4e00-\u9fa5]{2,6})(?:的)?天气", msg)
        city_name = city.group(1) if city else ""
        return f"{city_name}天气查询" if city_name else "实时天气查询"

    if any(w in msg for w in ("算一下", "计算", "求解", "数学", "加", "减", "乘", "除", "*", "/", "+", "-")):
        if "python" in msg.lower():
            return "Python 算术计算"
        return "数学运算求解"

    if "python" in msg.lower():
        return "Python 代码执行"
    if any(w in msg for w in ("搜索", "查找", "搜一下", "google", "百度")):
        return "网络信息检索"
    if any(w in msg for w in ("数据库", "sql", "mysql")):
        return "数据库查询分析"

    # 通用截取清理：去除常见语气动词与助词
    clean = re.sub(r"^(请问|帮我|看一下|查一下|用|如何|怎么|什么是|帮我算一下|算一下)\s*", "", msg)
    clean = re.sub(r"[？?！!。，,]", "", clean).strip()
    if len(clean) > 14:
        clean = clean[:12] + "…"
    return clean or "智能对话"


def fallback_conversation_title(user_message: str) -> str:
    return _summarize_rule_title(user_message)


def normalize_generated_title(raw: str, user_message: str) -> str:
    title = raw.strip().strip('"\'""''「」《》[]')
    title = re.sub(r"\s+", " ", title.split("\n")[0].strip())
    title = re.sub(r"[？?！!。，,]", "", title)
    title = _clean_title(title)
    if not title or len(title) > 20:
        return _summarize_rule_title(user_message)
    return title[:16]


async def generate_conversation_title(
    user_message: str,
    assistant_message: str = "",
    *,
    model_id: str | None = None,
) -> str:
    """使用大模型提炼总结会话标题，失败时降级为智能主题归纳"""
    import asyncio

    user_text = user_message.strip()
    if not user_text:
        return "新对话"

    try:
        llm = create_chat_model(model=model_id)
        prompt_content = f"用户提问：{user_text[:300]}"
        if assistant_message.strip():
            prompt_content += f"\n助手回答：{assistant_message[:300]}"

        resp = await asyncio.wait_for(
            llm.ainvoke(
                [
                    SystemMessage(content=_TITLE_PROMPT),
                    HumanMessage(content=prompt_content),
                ]
            ),
            timeout=3.0,
        )
        content = resp.content if isinstance(resp.content, str) else str(resp.content or "")
        return normalize_generated_title(content, user_text)
    except Exception:
        return _summarize_rule_title(user_text)
