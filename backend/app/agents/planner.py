"""app/agents/planner.py — Planner Agent + Intent Detection

注意（§3.1）：detect_intent 规则引擎已降级为回退策略（fallback）：
仅在模型不支持 Function Calling（如 Mock 模式）时生效；
主链路由 app/runtime/executor/tool_binding.py 的 FC 自主决策。
Prompt 拼装已收口至 ContextBuilder（§6.1）。
"""

from __future__ import annotations

import re

from app.core.context.state import AgentState, IntentType
from app.llm.factory import create_chat_model
from app.tools.compute.calculator import extract_expression, looks_like_calculation
from app.tools.text.tool_text import (
    extract_database_query,
    extract_file_query,
    extract_search_query,
    wants_file_list,
)

_CALC_HINT = re.compile(
    r"(计算|算一下|帮我算|请计算|calculate|calc|等于|是多少|多少)",
    re.IGNORECASE,
)

_DEV_VERBS = (
    "怎么开发",
    "如何开发",
    "怎样开发",
    "帮我开发",
    "帮我做",
    "帮我设计",
    "帮我搭建",
    "帮我写",
    "从零开发",
    "从0开发",
    "开发一个",
    "做一个",
    "设计一个",
    "搭建一个",
    "实现一个",
    "写一个",
    "生成一个",
)

_DESIGN_DOC_HINTS = (
    "设计文档",
    "设计方案",
    "需求文档",
    "技术文档",
    "开发文档",
    "架构设计",
    "技术方案",
    "实现方案",
    "开发方案",
    "技术栈",
)

_PROJECT_NAME_RE = re.compile(
    r"[\u4e00-\u9fa5a-zA-Z0-9]{2,24}(管理系统|管理平台|信息平台|业务平台|小程序|系统平台)"
)

_DEV_QUESTION_RE = re.compile(
    r"(怎么|如何|怎样|想要|想做|需要做).{0,12}(系统|平台|小程序|管理系统)"
)

_AGENTONE_CTX = ("agentone", "本系统", "本平台", "这个系统", "本助手", "知识库")

_SYSTEM_TARGETS = (
    "管理系统",
    "管理平台",
    "平台",
    "小程序",
    "erp",
    "saas",
    "商城",
    "外卖",
    "刷题",
    "图书管理",
    "学生管理",
    "教务",
    "仓储",
    "mes",
)


def _looks_like_prompt_engineering(text: str) -> bool:
    lowered = text.lower()
    if any(k in lowered for k in _AGENTONE_CTX):
        return False

    has_dev = any(v in text for v in _DEV_VERBS)
    has_target = any(t in lowered for t in _SYSTEM_TARGETS) or "系统" in text
    has_scheme = any(k in text for k in _DESIGN_DOC_HINTS)
    has_prompt = any(k in lowered for k in ("提示词", "prompt"))

    if has_dev and has_target:
        return True
    if has_target and has_scheme:
        return True
    if has_prompt and (has_dev or has_target):
        return True
    if "管理系统" in text and has_scheme:
        return True
    if _PROJECT_NAME_RE.search(text):
        return True
    if _DEV_QUESTION_RE.search(text):
        return True
    return False


def detect_intent(user_input: str) -> tuple[IntentType, str, dict]:
    text = user_input.strip()

    if _looks_like_prompt_engineering(text):
        return "prompt_engineer", "", {}

    lowered = text.lower()
    is_image_ctx = any(k in lowered for k in ("图片", "壁纸", "照片", "![", ".jpg", ".png", ".jpeg", ".webp", ".gif", "长发", "短发", "黑发", "金发"))
    if not is_image_ctx and (_CALC_HINT.search(text) or looks_like_calculation(text)):
        expression = extract_expression(text)
        if expression and re.search(r"\d", expression) and expression.lower() not in ("4k", "2k", "1080p"):
            return "calculator", "calculator", {"expression": expression}
    if any(k in lowered for k in ("搜索", "search", "查一下", "查询资料", "网上", "百度", "google", "duckduckgo", "搜一下", "搜", "帮我查")):
        return "search", "search", {"query": extract_search_query(text)}
    if any(k in lowered for k in ("文件", "读取", "上传", "file", "文档", "pdf", "excel")) or wants_file_list(text):
        return "file", "file", {"query": extract_file_query(text)}
    if any(
        k in lowered
        for k in (
            "数据库",
            "数据库表",
            "数据表",
            "有哪些表",
            "sql",
            "select",
            "from",
            "查询表",
            "有多少",
            "多少用户",
            "用户数",
            "会话数",
            "消息数",
            "消息总数",
            "统计",
            "audit",
            "tool_log",
            "日志",
            "注册",
        )
    ):
        return "database", "database", {"query": extract_database_query(text)}

    return "chat", "", {}


async def planner_node(state: AgentState) -> dict:
    meta = state.get("metadata") or {}
    user_input = state.get("user_input") or ""

    # 快速通道（性能）：纯对话 / 提示词工程 / 工具已禁用时无需规划，
    # 跳过 planner 的整段 LLM 往返，直接进入总结流式输出。
    tools_enabled = meta.get("enable_tools") is not False
    intent, _tool_name, _tool_input = detect_intent(user_input)
    if not tools_enabled or intent in ("chat", "prompt_engineer"):
        return {"current_node": "planner", "metadata": {"plan": ""}}

    model_id = meta.get("model_id")
    llm = create_chat_model(model=model_id, thinking_level=str(meta.get("thinking_level") or "standard"))

    from app.runtime.context.builder import get_context_builder

    messages, _context_state = get_context_builder().build("planner", dict(state))

    response = await llm.ainvoke(messages)
    plan = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "current_node": "planner",
        "metadata": {"plan": plan},
    }