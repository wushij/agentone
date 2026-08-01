"""backend/app/llm/mock.py"""

from __future__ import annotations

import asyncio
import re
from typing import Any, AsyncIterator, Iterator, Optional

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

_TECH_SECTION_PATTERN = re.compile(r"(?=前端采用|后端采用|数据存储|AI 能力|项目源码)")
_TECH_SECTION_MAP = (
    ("前端采用", "前端"),
    ("后端采用", "后端"),
    ("数据存储", "数据存储"),
    ("AI 能力", "AI 能力集成"),
    ("项目源码", "项目源码"),
)


def _linkify_inline(text: str) -> str:
    linked = re.sub(
        r"Gitee\s+(https?://[^\s，。；;\]]+)",
        r"[Gitee](\1)",
        text,
    )
    linked = re.sub(
        r"GitHub\s+(https?://[^\s，。；;\]]+)",
        r"[GitHub](\1)",
        linked,
    )
    return linked


def _format_tech_stack_answer(answer: str) -> str:
    """Layout: 📌 系统定位 → ⚙️ 技术架构 → 💡 项目源码"""
    text = answer.strip()
    sections = _TECH_SECTION_PATTERN.split(text)
    if len(sections) <= 1:
        return _format_generic_sections(answer)

    intro = sections[0].strip()
    if intro and not intro.endswith("。"):
        intro += "。"

    arch_lines: list[str] = []
    source_lines: list[str] = []

    for section in sections[1:]:
        section = section.strip().rstrip("，。；;")
        if not section:
            continue
        for prefix, label in _TECH_SECTION_MAP:
            if not section.startswith(prefix):
                continue
            body = section[len(prefix) :].lstrip("：:使用通过").strip()
            body = _linkify_inline(body)
            if prefix == "项目源码":
                gitee = re.search(r"Gitee\s+(https?://[^\s，。；;\]]+)", body)
                github = re.search(r"GitHub\s+(https?://[^\s，。；;\]]+)", body)
                if gitee:
                    source_lines.append(f"- **Gitee**：[Gitee]({gitee.group(1)})")
                if github:
                    source_lines.append(f"- **GitHub**：[GitHub]({github.group(1)})")
                if not source_lines:
                    source_lines.append(f"- **项目源码**：{_linkify_inline(body)}")
            else:
                arch_lines.append(f"- **{label}**：{body}")
            break

    lines = ["📌 **系统定位**", "", intro]
    if arch_lines:
        lines.extend(["", "⚙️ **技术架构**", ""] + arch_lines)
    if source_lines:
        lines.extend(["", "💡 **项目源码**", ""] + source_lines)
    return "\n".join(lines)


def _format_generic_sections(answer: str) -> str:
    text = _linkify_inline(answer.strip())
    if not text:
        return "当前知识库暂无该条目，可换关键词或联系管理员补充文档。"

    parts = [part.strip() for part in re.split(r"。+", text) if part.strip()]
    intro = f"{parts[0]}。" if parts else text
    lines = ["📌 **说明**", "", intro]

    if len(parts) > 1:
        lines.extend(["", "📋 **要点**", ""])
        for part in parts[1:]:
            clause = part.strip()
            if not clause:
                continue
            if clause.count("，") >= 2 and len(clause) > 40:
                for item in [c.strip() for c in clause.split("，") if c.strip()]:
                    lines.append(f"- {_linkify_inline(item.rstrip('。'))}")
            else:
                lines.append(f"- {_linkify_inline(clause)}。")
    return "\n".join(lines)


def _format_answer_markdown(answer: str) -> str:
    if _TECH_SECTION_PATTERN.search(answer):
        return _format_tech_stack_answer(answer)
    return _format_generic_sections(answer)


def _extract_rag_answer(context: str) -> str:
    if not context:
        return ""
    # 1. 优先提取显式的 "答：" 后续回答文本
    match = re.search(r"答[:：]\s*([\s\S]+?)(?=\n\n【|\n\n请基于|\n\n问[:：]|$)", context)
    if match and len(match.group(1).strip()) > 5:
        return match.group(1).strip()

    # 2. 提取【资料 X】格式的文本块
    match = re.search(r"【资料 \d+[^】]*】\s*([\s\S]+?)(?=\n\n【资料|\n\n请基于|\n\n【|$)", context)
    if match:
        block = match.group(1).strip()
        qa = re.search(r"答[:：]\s*([\s\S]+)$", block)
        if qa:
            return qa.group(1).strip()
        clean_block = re.sub(r"^[^\n]+\.md\s*", "", block).strip()
        if clean_block:
            return clean_block

    # 3. 提取【知识库参考资料】后的全量文案
    match = re.search(r"【知识库参考资料】\s*([\s\S]+?)(?=\n\n【调用的工具】|\n\n【记忆|$)", context)
    if match:
        block = match.group(1).strip()
        if block.startswith("（无）"):
            return ""
        qa = re.search(r"答[:：]\s*([\s\S]+)$", block)
        if qa:
            return qa.group(1).strip()
        clean_block = re.sub(r"^[^\n]+\.md\s*", "", block).strip()
        return clean_block or block

    return ""


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock-chat"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = self._build_reply(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=None, **kwargs)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        text = self._build_reply(messages)
        for char in text:
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        text = self._build_reply(messages)
        # 降低逐字人工延迟（性能）：每 4 个字符 sleep 一次，保留流式观感的同时显著减少总耗时
        for i, char in enumerate(text):
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))
            if i % 4 == 0:
                await asyncio.sleep(0.006)

    def _build_reply(self, messages: list[BaseMessage]) -> str:
        # 1. 收集全量消息文本（包含 SystemMessage 中的【知识库参考资料】）
        full_text = "\n\n".join(str(msg.content) for msg in messages)

        # 2. 提取用户最新的真实提问 (HumanMessage)
        raw_user_text = ""
        for msg in reversed(messages):
            if msg.type == "human":
                raw_user_text = str(msg.content).strip()
                break

        # 提取去掉上下文 Prompt 结构标签后的纯用户问题
        user_text = raw_user_text
        clean_match = re.search(r"【当前用户问题】\s*([\s\S]+?)(?=\n\n【|\n\n请基于|\n\n问[:：]|$)", raw_user_text)
        if clean_match:
            user_text = clean_match.group(1).strip()
        else:
            user_text = re.sub(r"【[^】]+】[\s\S]*$", "", user_text).strip()

        if not user_text:
            user_text = raw_user_text[:50]

        # 3.5 用户发送了图片或图片问答
        if any(k in raw_user_text.lower() for k in ("图片", ".jpg", ".png", ".webp", ".jpeg", ".gif", "![")):
            img_match = re.search(r"!\[(.*?)\]\((.*?)\)", raw_user_text)
            img_name = img_match.group(1) if img_match else "关联图片"
            return (
                f"📌 **图片处理**\n\n已成功接收并校验您上传的图片「{img_name}」。\n\n"
                "💡 **分析说明**\n\n图片文件已持久化存储至系统文件中心，并在当前对话中成功关联呈现。在 Mock 演示模式下已完成图像链路校验；配置具备视觉能力的模型（如 GPT-4o / Qwen-VL）后即可进行完整的图像内容深度解析。"
            )

        # 3. 如果包含知识库参考资料，优先提取 RAG 内容作答
        if "【知识库参考资料】" in full_text or "【资料 " in full_text or "知识库参考:" in full_text:
            answer = _extract_rag_answer(full_text)
            if answer:
                return _format_answer_markdown(answer)

        # 4. 天气类询问
        if any(k in user_text for k in ("天气", "气温", "下雨", "预报")):
            return (
                "📌 **天气查询**\n\n"
                "当前为 Mock 演示模式，暂未接入实时天气 API。\n\n"
                "💡 **提示**\n\n"
                "在【工具管理】中启用 SearchTool 或天气插件，并配置真实 API Key 后即可查询实时天气预报。"
            )

        # 5. 判别数学计算需求：必须是用户提问中显式含有数值和运算指令
        math_symbols = ("+", "-", "*", "/", "×", "÷")
        has_math_op = any(op in user_text for op in math_symbols) or ("算一下" in user_text or "计算" in user_text)
        is_real_math_question = (
            has_math_op
            and any(c.isdigit() for c in user_text)
            and not any(k in user_text for k in ("Agent", "系统", "架构", "知识库", "技术"))
        )

        if is_real_math_question:
            return (
                "📌 **结果**\n\n运算已完成，请查看上方工具输出。\n\n"
                "💡 **说明**\n\nMock 演示模式；配置真实 API Key 后可接入 DeepSeek 等模型。"
            )

        # 6. 用户提问包含 AgentOne 系统架构类问题
        if any(k in user_text for k in ("AgentOne", "架构", "系统", "技术")):
            return (
                "📌 **系统定位**\n\n"
                "AgentOne 是企业级 AI 智能体平台，提供对话、知识库 RAG、工具调用与工作流编排。\n\n"
                "⚙️ **技术架构**\n\n"
                "- **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus\n"
                "- **后端**：FastAPI + SQLAlchemy + LangGraph + LangChain\n"
                "- **数据存储**：MySQL 8 (主存储) 和 Redis 7 (缓存、分布式锁)\n"
                "- **AI 能力**：多模型协同、知识库 RAG 检索、工具链启停\n\n"
                "💡 **说明**\n\n当前为 Mock 演示；配置真实 DeepSeek API Key 后可获得更完整回答。"
            )

        # 7. 通用兜底
        if user_text:
            return (
                f"📌 **说明**\n\n关于「{user_text}」，当前为 Mock 演示模式。\n\n"
                "💡 **提示**\n\n配置真实 API Key 后可获得更丰富、准确的智能生成体验。"
            )

        return "你好，我是 AgentOne 助手（Mock 演示模式）。"
