"""backend/app/graph/nodes/summarizer_node.py"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import AgentState
from app.llm.factory import create_chat_model
from app.utils.prompt_loader import load_prompt

SUMMARIZER_PROMPT = load_prompt(
    "summary",
    "你是一个总结代理（Summary Agent / Summarizer Agent）。"
    "你需要整合任务规划、收集到的检索信息/工具执行结果以及审阅建议，"
    "为用户输出最终精美、易懂的回答。",
)


def _llm_for_state(state: AgentState):
    model_id = (state.get("metadata") or {}).get("model_id")
    return create_chat_model(model=model_id)


def _build_summarizer_messages(state: AgentState) -> list:
    user_input = state.get("user_input") or ""
    intent = state.get("intent") or "chat"
    if intent == "prompt_engineer":
        engineer_prompt = load_prompt(
            "prompt_engineer",
            "你是 AI 编程提示词工程专家，为用户生成企业级可投喂 AI 编程工具的开发提示词。",
        )
        context = (
            f"【用户需求】\n{user_input}\n\n"
            "【输出物定义】\n"
            "你要输出的是一份「可直接复制给 Cursor / GPT / Claude 执行的企业级终极开发提示词」，"
            "不是给用户看的简短设计摘要或通用框架说明。\n\n"
            "【硬性要求】\n"
            "1. 必须带 emoji，严格按 prompt_engineer 规范 §1～§6 全部章节展开（项目定位、技术栈、架构、"
            "AgentOne UI 规范含靛蓝主题/长圆边框/表头居中/侧边栏、功能模块、数据库文字描述）\n"
            "2. 数据库章节只用表格/列表文字说明表名、字段、关系，禁止写 CREATE TABLE / SQL 建表脚本。章节标题必须是简洁的 '# 💾 6. 数据库设计' 或 '# 💾 6. 数据库设计要求'，绝对禁止带有任何 '(文字描述版)' 或类似后缀。请以面向下游 AI 的指令格式书写（例如：'请在实现阶段根据以下表结构自动生成 SQL'），严禁包含任何面向当前用户的对话式解释、提示或免责声明（如‘注意：以下仅用文字描述...无需在提示词中编写...’）。\n"
            "3. 篇幅须足够长（通常不少于 2000 字），可直接投喂 AI 编程工具生成完整项目\n"
            "4. 禁止：只给几段概述、禁止「典型框架」「如需技术栈请告知」等敷衍结语\n"
            "5. 禁止：输出当前对话式的建议或解释说明；只输出给 AI 编程工具用的开发指令正文。严禁包含任何前言（如'以下是...'）或尾部结语/动作引导（如'以上即为生成的...请复制给 Cursor...'）。绝对禁止使用 Markdown 引用块（`>`）或带有对话提示倾向的独立指令框（如 `【指令】...`）来包裹最后的开发指令。确保指令以正常的 Markdown 章节标题（如 `# 🛠️ 7. 开发实施与编译指令`）和正文格式输出，回答 100% 是可以直接复制使用的纯净提示词正文。\n"
            "6. 根据用户提到的具体系统名称（如学生管理系统）填入全部章节，不得留空模板"
        )
        return [
            SystemMessage(content=engineer_prompt),
            HumanMessage(content=context),
        ]

    meta = state.get("metadata") or {}
    plan = meta.get("plan") or ""
    rag_context = meta.get("rag_context") or ""
    kb_ids = meta.get("kb_ids") or []
    kb_mounted = bool(kb_ids)
    tool_name = state.get("tool_name") or ""
    tool_result = state.get("tool_result") or ""
    review = meta.get("review") or ""

    if kb_mounted:
        kb_status = f"已挂载 {len(kb_ids)} 个知识库"
        if rag_context:
            kb_instruction = "有知识库参考时优先忠实转述；有工具结果时数字不得改动。"
        else:
            kb_instruction = (
                "知识库已检索但未命中相关资料，请仍用大模型正常完整作答；"
                "勿整段只回复「知识库暂无该条目」。"
            )
    else:
        kb_status = "未挂载（请基于模型知识与工具结果直接作答）"
        kb_instruction = "按常规模型能力作答即可。"

    context = (
        f"【当前用户问题】\n{user_input}\n\n"
        f"【知识库挂载状态】\n{kb_status}\n\n"
        f"【规划计划】\n{plan or '（无）'}\n\n"
        f"【知识库参考资料】\n{rag_context or '（无）'}\n\n"
        f"【调用的工具】\n{tool_name or '（无）'}\n\n"
        f"【工具结果】\n{tool_result or '（无）'}\n\n"
        f"【审核结果】\n{review or '（无）'}\n\n"
        f"请按人设 §4 排版规则输出最终回答。{kb_instruction}"
    )
    return [
        SystemMessage(content=SUMMARIZER_PROMPT),
        *state.get("messages", []),
        HumanMessage(content=context),
    ]


async def stream_summarizer_tokens(state: AgentState):
    llm = _llm_for_state(state)
    messages = _build_summarizer_messages(state)
    async for chunk in llm.astream(messages):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if delta:
            yield delta
