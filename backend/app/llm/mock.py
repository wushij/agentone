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
    match = re.search(r"答[:：]\s*([\s\S]+?)(?=\n\n【资料|\n\n请基于|$)", context)
    if match:
        return match.group(1).strip()
    match = re.search(r"【资料 \d+】\s*([\s\S]+?)(?=\n\n【资料|\n\n请基于|$)", context)
    if match:
        block = match.group(1).strip()
        qa = re.search(r"答[:：]\s*([\s\S]+)$", block)
        return (qa.group(1) if qa else block).strip()
    match = re.search(r"【知识库参考资料】\s*([\s\S]+?)(?=\n\n【调用的工具】|$)", context)
    if match:
        block = match.group(1).strip()
        if block.startswith("（无）"):
            return ""
        qa = re.search(r"答[:：]\s*([\s\S]+)$", block)
        return (qa.group(1) if qa else block).strip()
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
        for char in text:
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))
            await asyncio.sleep(0.005)

    def _build_reply(self, messages: list[BaseMessage]) -> str:
        user_text = ""
        for msg in reversed(messages):
            if msg.type == "human":
                user_text = str(msg.content)
                break
        if not user_text:
            return "你好，我是 AgentOne 助手（Mock 演示模式）。"

        if "计算" in user_text or any(op in user_text for op in "+-×÷*/"):
            return (
                "📌 **结果**\n\n运算已完成，请查看上方工具输出。\n\n"
                "💡 **说明**\n\nMock 演示模式；配置真实 API Key 后可接入 DeepSeek 等模型。"
            )

        if "知识库参考:" in user_text or "【知识库参考资料】" in user_text:
            answer = _extract_rag_answer(user_text)
            if answer:
                return _format_answer_markdown(answer)

        question = ""
        q_match = re.search(r"【当前用户问题】\s*\n(.+?)(?:\n\n|$)", user_text)
        if not q_match:
            q_match = re.search(r"用户问题:\s*(.+?)(?:\n|$)", user_text)
        if q_match:
            question = q_match.group(1).strip()

        if question:
            return (
                f"📌 **说明**\n\n关于「{question}」，当前为 Mock 演示。\n\n"
                "💡 **提示**\n\n请挂载知识库并使用 RAG 模式；配置 DeepSeek API Key 后可获得真实排版回复。"
            )

        if "AgentOne" in user_text or "架构" in user_text or "系统" in user_text:
            return (
                "📌 **系统定位**\n\n"
                "AgentOne 是企业级 AI 智能体平台，提供对话、知识库 RAG、工具调用与工作流编排。\n\n"
                "⚙️ **技术架构**\n\n"
                "- **前端**：Vue 3 + Element Plus\n"
                "- **后端**：FastAPI + LangGraph\n"
                "- **数据存储**：SQLite / 可扩展向量库\n"
                "- **AI 能力**：多模型接入、RAG、Tool 调用\n\n"
                "💡 **说明**\n\n当前为 Mock 演示；配置真实模型后可获得更完整回答。"
            )

        return (
            f"📌 **说明**\n\n你好，收到你的消息。\n\n"
            "💡 **提示**\n\n当前为 Mock 演示；配置真实模型后可获得完整回答。"
        )
