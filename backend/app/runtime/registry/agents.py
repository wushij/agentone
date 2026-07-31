"""app/runtime/registry/agents.py — Agent Registry（§15.1）

Agent 不再是硬编码的类，而是可注册、可发现、可按能力标签路由的资源。
Supervisor 从 Registry 按 capability 发现候选子 Agent，而非硬编码枚举。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentManifest:
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)  # 能力标签，供 Supervisor 发现
    tools: list[str] = field(default_factory=list)         # 绑定工具名（空=全部可用工具）
    persona: str = ""                                       # 子 Agent 系统提示词
    model_role: str = "react"                               # Model Router 角色
    version: str = "1.0.0"


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentManifest] = {}

    def register(self, manifest: AgentManifest) -> None:
        self._agents[manifest.name] = manifest

    def get(self, name: str) -> AgentManifest | None:
        return self._agents.get(name)

    def remove(self, name: str) -> None:
        self._agents.pop(name, None)

    def list(self, capability: str | None = None) -> list[AgentManifest]:
        items = list(self._agents.values())
        if capability:
            items = [m for m in items if capability in m.capabilities]
        return items

    def catalog(self) -> str:
        """供 Supervisor 决策的候选清单文本。"""
        lines = []
        for m in self._agents.values():
            caps = "、".join(m.capabilities) or "通用"
            lines.append(f"- {m.name}：{m.description}（擅长：{caps}）")
        return "\n".join(lines)


_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        _register_builtin_agents(_registry)
    return _registry


def _register_builtin_agents(reg: AgentRegistry) -> None:
    """内置子 Agent 清单。工具名对齐 app/tools/registry 与新增高价值工具。"""
    reg.register(AgentManifest(
        name="coder",
        description="代码编写、执行与自测",
        capabilities=["coding", "compute", "debug"],
        tools=["python_executor", "calculator"],
        persona=(
            "你是资深工程师 Agent。用 python_executor 编写并执行代码解决问题，"
            "先写代码再运行验证，输出结论与关键代码。"
        ),
        model_role="coder",
    ))
    reg.register(AgentManifest(
        name="analyst",
        description="数据查询、统计与可视化",
        capabilities=["data", "analysis", "chart"],
        tools=["database", "chart", "calculator"],
        persona=(
            "你是数据分析 Agent。用 database 查询数据、calculator 计算、chart 生成图表，"
            "产出带图表的分析结论。"
        ),
        model_role="analyst",
    ))
    reg.register(AgentManifest(
        name="researcher",
        description="联网检索与资料汇总",
        capabilities=["search", "research", "web"],
        tools=["search", "http_request", "file"],
        persona="你是调研 Agent。用 search/http_request 检索资料并忠实汇总，标注来源。",
        model_role="react",
    ))
    reg.register(AgentManifest(
        name="general",
        description="通用助手（可调用全部工具）",
        capabilities=["general", "chat"],
        tools=[],  # 空=全部可用工具
        persona="你是通用助手 Agent，可调用任意可用工具解决用户问题。",
        model_role="react",
    ))
