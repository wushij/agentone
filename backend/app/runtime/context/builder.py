"""app/runtime/context/builder.py — Context Builder（§6.1）

唯一的 Prompt 拼装出口：planner / reviewer / summarizer(writer) / react_agent
全部经此构建消息，收口原先散落在三个 Agent 文件里的手写 f-string。
每次构建产出 ContextState（注入了哪些块、各占多少 token）供调试面板可视化。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.runtime.context.budget import BudgetReport, ContextBlock, TokenBudget, count_tokens
from app.utils.prompt_loader import load_prompt

# 各角色默认提示词（DB/文件优先，此处为兜底）
_ROLE_FALLBACKS = {
    "planner": (
        "你是一个任务规划代理（Planner Agent）。"
        "分析用户的输入，判断要解决这个问题需要哪些步骤，并生成一个简洁明了的步骤规划。"
    ),
    "reviewer": (
        "你是一个结果审阅代理（Reviewer Agent）。"
        "你需要审查收集到的信息和工具执行结果是否能够准确解答用户的问题。"
        "如果结果正确，请输出 'APPROVED' 以及简要说明；如果结果有误或不完整，请说明具体问题。"
    ),
    "summary": (
        "你是一个总结代理（Summary Agent / Summarizer Agent）。"
        "你需要整合任务规划、收集到的检索信息/工具执行结果以及审阅建议，为用户输出最终精美、易懂的回答。\n"
        "【排版规范】回答时请务必使用丰富直观的 Emoji 图标进行标题分节（例如：📌 核心概述、⚙️ 技术架构、💡 项目源码、📋 功能说明、🔍 详细解答等），并配合 Markdown 列表进行结构化清晰排版。"
    ),
    "react_agent": (
        "你是 AgentOne 的执行代理。你可以调用提供的工具来解决用户问题；"
        "可以多步调用不同工具（先搜索、再计算、再查库等），当已有足够信息时直接给出最终回答，不要重复调用相同工具。\n"
        "【排版规范】回答时请务必使用丰富直观的 Emoji 图标进行标题分节（例如：📌 核心概述、⚙️ 技术架构、💡 项目源码、📋 功能说明、🔍 详细解答等），并配合 Markdown 列表进行结构化清晰排版。"
    ),
    "prompt_engineer": "你是 AI 编程提示词工程专家，为用户生成企业级可投喂 AI 编程工具的开发提示词。",
}


def _thinking_directive(state: dict[str, Any]) -> str:
    """扩展思考档位（§6.1）→ 注入到 system 提示的推理指令，对任意 provider 都生效。"""
    level = str((state.get("metadata") or {}).get("thinking_level") or "standard")
    if level == "fast":
        return "【快速模式】直接给出简洁、准确的结论，减少推理铺垫；但仍保持 emoji 分节与 Markdown 排版。"
    if level == "extended":
        return (
            "【深度思考模式】在给出最终答案前，先系统性地分步推理：拆解问题、"
            "权衡多种方案、检查边界与反例，再输出严谨、完整、有依据的结论。"
        )
    return ""


class ContextBuilder:
    """ContextBuilder.build(role, state) → (messages, context_state)"""

    def __init__(self, budget: TokenBudget | None = None):
        self.budget = budget or TokenBudget()

    # ---------- 对外主入口 ----------

    def build(self, role: str, state: dict[str, Any]) -> tuple[list[BaseMessage], dict[str, Any]]:
        if role == "planner":
            return self._build_planner(state)
        if role == "reviewer":
            return self._build_reviewer(state)
        if role in ("summarizer", "writer", "summary"):
            return self._build_summarizer(state)
        if role == "react_agent":
            return self._build_react_agent(state)
        raise ValueError(f"未知的 Prompt 角色: {role}")

    # ---------- planner ----------

    def _build_planner(self, state: dict[str, Any]) -> tuple[list[BaseMessage], dict[str, Any]]:
        report = BudgetReport(total=self.budget.total)
        system = load_prompt("planner", _ROLE_FALLBACKS["planner"])
        directive = _thinking_directive(state)
        if directive:
            system = directive + "\n\n" + system
        sys_block = self.budget.fit_text("system", system, "system")
        report.blocks.append(sys_block)

        user_input = str(state.get("user_input") or "")
        human = f"用户输入: {user_input}"
        report.blocks.append(ContextBlock(name="user_input", content="", tokens=count_tokens(human)))

        messages: list[BaseMessage] = [SystemMessage(content=sys_block.content), HumanMessage(content=human)]
        return messages, report.to_context_state()

    # ---------- reviewer ----------

    def _build_reviewer(self, state: dict[str, Any]) -> tuple[list[BaseMessage], dict[str, Any]]:
        report = BudgetReport(total=self.budget.total)
        system = load_prompt("reviewer", _ROLE_FALLBACKS["reviewer"])
        sys_block = self.budget.fit_text("system", system, "system")
        report.blocks.append(sys_block)

        meta = state.get("metadata") or {}
        tool_result_block = self.budget.fit_text("tool_result", str(state.get("tool_result") or ""), "rag")
        report.blocks.append(tool_result_block)

        context = (
            f"用户问题: {state.get('user_input') or ''}\n"
            f"规划步骤: {meta.get('plan') or ''}\n"
            f"执行工具: {state.get('tool_name') or ''}\n"
            f"工具返回结果: {tool_result_block.content or '（无）'}\n"
            f"工具报错信息: {state.get('tool_error') or '（无）'}"
        )
        report.blocks.append(ContextBlock(name="review_context", content="", tokens=count_tokens(context)))

        messages: list[BaseMessage] = [SystemMessage(content=sys_block.content), HumanMessage(content=context)]
        return messages, report.to_context_state()

    # ---------- summarizer（含 prompt_engineer 分支，迁自 writer._build_summarizer_messages） ----------

    def _build_summarizer(self, state: dict[str, Any]) -> tuple[list[BaseMessage], dict[str, Any]]:
        user_input = str(state.get("user_input") or "")
        intent = state.get("intent") or "chat"
        if intent == "prompt_engineer":
            return self._build_prompt_engineer(user_input)

        report = BudgetReport(total=self.budget.total)
        system = load_prompt("summary", _ROLE_FALLBACKS["summary"])
        directive = _thinking_directive(state)
        if directive:
            system = directive + "\n\n" + system
        sys_block = self.budget.fit_text("system", system, "system")
        report.blocks.append(sys_block)

        meta = state.get("metadata") or {}
        plan = str(meta.get("plan") or "")
        kb_ids = meta.get("kb_ids") or []
        kb_mounted = bool(kb_ids)
        review = str(meta.get("review") or "")
        tool_name = str(state.get("tool_name") or "")

        # 记忆块（Memory Manager 召回，§6.1 [Memory]）
        memory_text = str(meta.get("memory_context") or "")
        memory_block = self.budget.fit_text("memory", memory_text, "memory")
        if memory_text:
            report.blocks.append(memory_block)

        # RAG 块
        rag_block = self.budget.fit_text("rag", str(meta.get("rag_context") or ""), "rag")
        report.blocks.append(rag_block)

        # 工具结果块（超长压缩为截断）
        tool_block = self.budget.fit_text("tool_result", str(state.get("tool_result") or ""), "rag")
        report.blocks.append(tool_block)

        # 工具轨迹（ReAct scratchpad）
        scratchpad_text = str(meta.get("scratchpad_text") or "")
        scratchpad_block = self.budget.fit_text("scratchpad", scratchpad_text, "memory")
        if scratchpad_text:
            report.blocks.append(scratchpad_block)

        if kb_mounted:
            kb_status = f"已挂载 {len(kb_ids)} 个知识库"
            if rag_block.content:
                kb_instruction = "有知识库参考时优先忠实转述；有工具结果时数字不得改动。"
            else:
                kb_instruction = (
                    "知识库已检索但未命中相关资料，请仍用大模型正常完整作答；"
                    "勿整段只回复「知识库暂无该条目」。"
                )
        else:
            kb_status = "未挂载（请基于模型知识与工具结果直接作答）"
            kb_instruction = "按常规模型能力作答即可。"

        parts = [
            f"【当前用户问题】\n{user_input}",
            f"【知识库挂载状态】\n{kb_status}",
            f"【规划计划】\n{plan or '（无）'}",
        ]
        if memory_block.content:
            parts.append(f"【记忆上下文】\n{memory_block.content}")
        parts.append(f"【知识库参考资料】\n{rag_block.content or '（无）'}")
        if scratchpad_block.content:
            parts.append(f"【工具调用轨迹】\n{scratchpad_block.content}")
        parts.append(f"【调用的工具】\n{tool_name or '（无）'}")
        parts.append(f"【工具结果】\n{tool_block.content or '（无）'}")
        parts.append(f"【审核结果】\n{review or '（无）'}")
        parts.append(f"【排版要求】请用 📌 / ⚙️ / 📋 / 💡 等 emoji 分节标题 + Markdown 列表/表格，输出结构清晰、精美易读的最终回答。{kb_instruction}")
        context = "\n\n".join(parts)

        # 历史消息滚动窗口
        history, history_block = self.budget.fit_history(list(state.get("messages") or []))
        report.blocks.append(history_block)

        messages: list[BaseMessage] = [
            SystemMessage(content=sys_block.content),
            *history,
            HumanMessage(content=context),
        ]
        return messages, report.to_context_state()

    def _build_prompt_engineer(self, user_input: str) -> tuple[list[BaseMessage], dict[str, Any]]:
        report = BudgetReport(total=self.budget.total)
        engineer_prompt = load_prompt("prompt_engineer", _ROLE_FALLBACKS["prompt_engineer"])
        sys_block = self.budget.fit_text("system", engineer_prompt, "system")
        report.blocks.append(sys_block)

        context = (
            f"【用户需求】\n{user_input}\n\n"
            "【输出物定义】\n"
            "你要输出的是一份「可直接复制给 Cursor / GPT / Claude 执行的企业级终极开发提示词」，"
            "不是给用户看的简短设计摘要或通用框架说明。\n\n"
            "【硬性要求】\n"
            "1. 必须带 emoji，严格按 prompt_engineer 规范 §1～§6 全部章节展开（项目定位、技术栈、架构、"
            "AgentOne UI 规范含靛蓝主题/长圆边框/表头居中/侧边栏、功能模块、数据库文字描述）\n"
            "2. 数据库章节只用表格/列表文字说明表名、字段、关系，禁止写 CREATE TABLE / SQL 建表脚本。章节标题必须是简洁的 '# 💾 6. 数据库设计' 或 '# 💾 6. 数据库设计要求'，绝对禁止带有任何 '(文字描述版)' 或类似后缀。请以面向下游 AI 的指令格式书写（例如：'请在实现阶段根据以下表结构自动生成 SQL'），严禁包含任何面向当前用户的对话式解释、提示或免责声明（如'注意：以下仅用文字描述...无需在提示词中编写...'）。\n"
            "3. 篇幅须足够长（通常不少于 2000 字），可直接投喂 AI 编程工具生成完整项目\n"
            "4. 禁止：只给几段概述、禁止「典型框架」「如需技术栈请告知」等敷衍结语\n"
            "5. 禁止：输出当前对话式的建议或解释说明；只输出给 AI 编程工具用的开发指令正文。严禁包含任何前言（如'以下是...'）或尾部结语/动作引导（如'以上即为生成的...请复制给 Cursor...'）。绝对禁止使用 Markdown 引用块（`>`）或带有对话提示倾向的独立指令框（如 `【指令】...`）来包裹最后的开发指令。确保指令以正常的 Markdown 章节标题（如 `# 🛠️ 7. 开发实施与编译指令`）和正文格式输出，回答 100% 是可以直接复制使用的纯净提示词正文。\n"
            "6. 根据用户提到的具体系统名称（如学生管理系统）填入全部章节，不得留空模板"
        )
        report.blocks.append(ContextBlock(name="engineer_context", content="", tokens=count_tokens(context)))

        messages: list[BaseMessage] = [SystemMessage(content=sys_block.content), HumanMessage(content=context)]
        return messages, report.to_context_state()

    # ---------- react_agent（FC 循环的决策消息） ----------

    def _build_react_agent(self, state: dict[str, Any]) -> tuple[list[BaseMessage], dict[str, Any]]:
        report = BudgetReport(total=self.budget.total)
        system = load_prompt("react_agent", _ROLE_FALLBACKS["react_agent"])
        meta = state.get("metadata") or {}
        directive = _thinking_directive(state)
        if directive:
            system = directive + "\n\n" + system

        extras: list[str] = []
        rag_block = self.budget.fit_text("rag", str(meta.get("rag_context") or ""), "rag")
        if rag_block.content:
            report.blocks.append(rag_block)
            extras.append(f"【知识库参考资料】\n{rag_block.content}")
        memory_block = self.budget.fit_text("memory", str(meta.get("memory_context") or ""), "memory")
        if memory_block.content:
            report.blocks.append(memory_block)
            extras.append(f"【记忆上下文】\n{memory_block.content}")
        if extras:
            system = system + "\n\n" + "\n\n".join(extras)

        sys_block = self.budget.fit_text("system", system, "system")
        report.blocks.append(sys_block)

        history, history_block = self.budget.fit_history(list(state.get("messages") or []))
        report.blocks.append(history_block)

        messages: list[BaseMessage] = [
            SystemMessage(content=sys_block.content),
            *history,
        ]
        user_input = str(state.get("user_input") or "")
        if user_input:
            messages.append(HumanMessage(content=user_input))
        return messages, report.to_context_state()


_builder: ContextBuilder | None = None


def get_context_builder() -> ContextBuilder:
    global _builder
    if _builder is None:
        _builder = ContextBuilder()
    return _builder
