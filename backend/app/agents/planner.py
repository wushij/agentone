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


def _detect_multimodal(text: str, lowered: str) -> tuple[IntentType, str, dict] | None:
    """多模态意图识别（传统图路径）：关键词力求特异避免误伤；文件由工具自行定位。"""
    if "ocr" in lowered or any(k in text for k in ("提取文字", "识别文字", "识别图中", "发票", "身份证", "票据识别", "文字提取")):
        return "ocr", "ocr_extract", {"query": ""}
    if "关键帧" in text or ("视频" in text and any(k in text for k in ("分析", "识别", "内容", "画面", "看看", "描述"))):
        return "video", "video_analyze", {"question": text}
    if any(k in text for k in ("转写", "语音转文字", "音频转", "录音转", "会议记录", "语音识别")):
        return "audio", "audio_transcribe", {"query": ""}
    # 附带图片（前端将图片拼成 markdown ![](.../download?token=xxx)）→ 优先路由到视觉工具；或显式看图自然关键词
    has_img_md = bool(re.search(r"!\[[^\]]*\]\([^)]+\)", text))
    if has_img_md or any(k in text for k in ("看看这张", "这张图", "这张照片", "图片里", "图片中", "图片多少", "图片内容", "分析图片", "识别图片", "看图", "图中", "图里", "画面里", "照片里", "照片中", "这是什么图", "长发", "短发", "黑发", "金发", "发型", "多少个", "多少人")):
        return "image", "image_analyze", {"question": text}
    if any(k in text for k in ("总结文档", "文档摘要", "摘要文档", "文档总结", "文档问答", "总结一下文档", "文档里讲")):
        return "document", "document_qa", {"question": text}
    return None


def extract_weather_city(text: str) -> str:
    cleaned = re.sub(r"(搜索|查一下|查询|帮我查|看看|下|现在的|今天|明天|后天|实时|城市)", "", text)
    cleaned = re.sub(r"(的天气|天气|气温|天气预报|预报|怎么样|如何|怎么样呢|的呢|呢|情况|状况)", "", cleaned).strip()
    cleaned = re.sub(r"^[^\u4e00-\u9fa5a-zA-Z]+|[^\u4e00-\u9fa5a-zA-Z]+$", "", cleaned)
    return cleaned if len(cleaned) >= 2 else (cleaned or "北京")


def detect_intent(user_input: str, history: list | None = None) -> tuple[IntentType, str, dict]:
    text = user_input.strip()

    if _looks_like_prompt_engineering(text):
        return "prompt_engineer", "", {}

    lowered = text.lower()
    mm = _detect_multimodal(text, lowered)
    if mm is not None:
        return mm

    # 1. 显式天气意图：包含“天气”、“气温”、“下雨”、“预报”
    has_explicit_weather = any(k in lowered for k in ("天气", "气温", "下雨", "预报"))

    # 2. 地名追问意图：如“佛山的呢”、“河源的呢”、“三亚呢”
    # 过滤非地名科技/通用词（如 vue3框架怎么样、React性能如何）
    _NON_CITY_KEYWORDS = (
        "多少", "什么", "算", "计算", "系统", "架构", "框架", "前端", "后端",
        "代码", "程序", "算法", "部署", "项目", "技术", "软件", "应用", "库",
        "模块", "组件", "手机", "电脑", "游戏", "模型", "大模型", "llm", "ai",
        "api", "界面", "功能", "设计", "体验", "性能", "vue", "react", "angular",
        "node", "java", "python", "js", "ts", "css", "html", "vite", "webpack",
    )
    has_followup_suffix = any(text.endswith(s) for s in ("呢", "的呢", "怎么样", "如何"))
    extracted_city = extract_weather_city(text)
    is_valid_city_followup = (
        has_followup_suffix
        and (2 <= len(extracted_city) <= 6)
        and not any(k in lowered for k in _NON_CITY_KEYWORDS)
    )

    is_image_ctx = any(k in lowered for k in ("图片", "壁纸", "照片", "![", ".jpg", ".png", ".jpeg", ".webp", ".gif", "长发", "短发", "黑发", "金发"))
    if not is_image_ctx and (_CALC_HINT.search(text) or looks_like_calculation(text)):
        expression = extract_expression(text)
        if expression and re.search(r"\d", expression) and expression.lower() not in ("4k", "2k", "1080p"):
            return "calculator", "calculator", {"expression": expression}

    if has_explicit_weather or is_valid_city_followup:
        return "search", "WeatherTool", {"city": extracted_city}

    # 3. URL 网址/网页调取意图：捕获包含 http:// 或 https:// 的网址
    url_match = re.search(r"https?://[^\s\u4e00-\u9fa5]+", text)
    if url_match:
        target_url = url_match.group(0).rstrip(".,;!?()[]<>\"'")
        return "http_request", "http_request", {"url": target_url, "method": "GET"}

    # 4. 搜索与网页查阅意图
    search_keywords = (
        "搜索", "search", "查一下", "查询资料", "网上", "百度", "google", "duckduckgo",
        "搜一下", "搜", "帮我查", "查阅", "访问", "打开", "看下网页", "抓取", "爬取",
        "解析链接", "网页", "网址", "链接"
    )
    if any(k in lowered for k in search_keywords):
        return "search", "search", {"query": extract_search_query(text)}

    if any(k in lowered for k in ("文件", "读取", "上传", "file", "文档", "pdf", "excel")) or wants_file_list(text):
        return "file", "file", {"query": extract_file_query(text)}

    # 5. 数据库只读查询意图（精细化匹配，严格区分 Python 代码中的 from/import 与 SQL 查询）
    is_code_snippet = bool(re.search(r"^\s*(from|import|def|class|async\s+def)\b|```|分析代码|解释代码|看下代码|检视代码", text, re.MULTILINE | re.IGNORECASE))
    has_sql_pattern = bool(re.search(r"\bselect\s+.+\s+from\b|\bshow\s+tables\b|\bdesc\s+\w+", lowered))
    explicit_db_keywords = (
        "数据库", "数据库表", "数据表", "有哪些表", "sql查询", "查数据库",
        "有多少用户", "用户数", "会话数", "消息总数"
    )
    if not is_code_snippet and (has_sql_pattern or any(k in lowered for k in explicit_db_keywords)):
        return "database", "database", {"query": extract_database_query(text)}

    return "chat", "", {}


async def planner_node(state: AgentState) -> dict:
    meta = state.get("metadata") or {}
    user_input = state.get("user_input") or ""

    tools_enabled = meta.get("enable_tools") is not False
    intent, tool_name, tool_input = detect_intent(user_input)

    # 1. 纯对话 / 提示词工程：无需工具规划，快速通过
    if not tools_enabled or intent in ("chat", "prompt_engineer"):
        return {"current_node": "planner", "metadata": {"plan": "普通对话意图，直接回答"}}

    # 2. 具备明确关联工具（如 WeatherTool / Calculator / Search / File / Database）：
    # 直接输出结构化确定性规划，消除 6.6 秒无谓的大模型往返与幻觉矛盾
    if tool_name:
        if tool_name == "WeatherTool":
            city = tool_input.get("city") or "指定城市"
            plan_desc = f"计划调用 WeatherTool 天气查询工具，实时检索「{city}」的当前气温、天气状况与降水提醒。"
        elif tool_name == "calculator":
            plan_desc = f"计划调用计算器工具，精确求解数学表达式: {tool_input.get('expression')}"
        elif tool_name == "search":
            plan_desc = f"计划调用网络搜索工具，检索资料: {tool_input.get('query')}"
        elif tool_name == "database":
            plan_desc = f"计划查询只读数据库，检索信息: {tool_input.get('query')}"
        else:
            plan_desc = f"识别到 {intent} 意图，计划调用工具 {tool_name}，参数: {tool_input}"

        return {
            "current_node": "planner",
            "metadata": {"plan": plan_desc},
        }

    # 3. 复杂推理场景：调用大模型进行深层逻辑规划
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