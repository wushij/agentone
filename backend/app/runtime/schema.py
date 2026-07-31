"""app/runtime/schema.py — 统一 AgentOutput Schema（§12.1）

所有 Agent/工作流最终输出收敛为一个结构，前端渲染、评测、API 消费全部统一。
阶段2 落地 answer/sources/metrics 核心字段；artifacts 等留待第三组。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    index: int
    kb_id: str = ""
    kb_name: str = ""
    file_name: str = ""
    score: float = 0.0
    text: str = ""


class ToolCallRecord(BaseModel):
    tool: str
    args: dict = Field(default_factory=dict)
    output: str = ""
    error: str = ""
    duration_ms: int = 0


class OutputMetrics(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    iterations: int = 0


class AgentOutput(BaseModel):
    answer: str = ""
    confidence: float | None = None
    sources: list[SourceRef] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    metrics: OutputMetrics = Field(default_factory=OutputMetrics)

    @staticmethod
    def source_refs_from_chunks(chunks: list[dict]) -> list[SourceRef]:
        refs: list[SourceRef] = []
        for i, c in enumerate(chunks, 1):
            refs.append(
                SourceRef(
                    index=i,
                    kb_id=str(c.get("kbId", "")),
                    kb_name=str(c.get("kbName", "")),
                    file_name=str(c.get("fileName", "")),
                    score=float(c.get("score", 0.0) or 0.0),
                    text=str(c.get("text", ""))[:500],
                )
            )
        return refs
