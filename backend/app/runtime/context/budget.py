"""app/runtime/context/budget.py — Token 预算器（§6.2）

- tiktoken 真实计数（不可用时回退 len//4 估算）
- 按模型窗口分段预算：system 15% / 记忆 10% / RAG 30% / 历史 30% / 留白 15%
- 落地 maxContext 配置项（settings_store）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_encoder = None
_encoder_failed = False


def count_tokens(text: str) -> int:
    """真实 tokenizer 计数；tiktoken 不可用（离线/未装）时回退估算。"""
    global _encoder, _encoder_failed
    if not text:
        return 0
    if not _encoder_failed and _encoder is None:
        try:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoder_failed = True
    if _encoder is not None:
        try:
            return len(_encoder.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)


# 分段预算比例（§6.2）
BUDGET_RATIOS = {
    "system": 0.15,
    "memory": 0.10,
    "rag": 0.30,
    "history": 0.30,
    # 剩余 15% 留白给模型输出
}


def resolve_max_context() -> int:
    """读取 maxContext 配置（settings_store → 默认 8192）。"""
    try:
        from app.services.system.settings_store import settings_store

        return int(settings_store.get("maxContext", 8192))
    except Exception:
        return 8192


@dataclass
class ContextBlock:
    name: str
    content: str
    tokens: int = 0
    truncated: bool = False


@dataclass
class BudgetReport:
    total: int
    blocks: list[ContextBlock] = field(default_factory=list)

    @property
    def used(self) -> int:
        return sum(b.tokens for b in self.blocks)

    def to_context_state(self) -> dict[str, Any]:
        return {
            "blocks": [
                {"name": b.name, "tokens": b.tokens, "truncated": b.truncated}
                for b in self.blocks
            ],
            "budget_total": self.total,
            "budget_used": self.used,
        }


class TokenBudget:
    def __init__(self, max_context: int | None = None):
        self.total = max_context or resolve_max_context()

    def limit_for(self, segment: str) -> int:
        ratio = BUDGET_RATIOS.get(segment, 0.10)
        return max(256, int(self.total * ratio))

    def fit_text(self, name: str, text: str, segment: str) -> ContextBlock:
        """单块文本按段预算裁剪（尾部截断 + 标记）。"""
        limit = self.limit_for(segment)
        tokens = count_tokens(text)
        if tokens <= limit:
            return ContextBlock(name=name, content=text, tokens=tokens)
        # 按比例截断（字符近似），保留头部
        keep_chars = max(64, int(len(text) * limit / tokens))
        truncated = text[:keep_chars] + "\n…（超出预算已截断）"
        return ContextBlock(name=name, content=truncated, tokens=count_tokens(truncated), truncated=True)

    def fit_history(self, messages: list[Any]) -> tuple[list[Any], ContextBlock]:
        """历史消息滚动窗口：从最新往前保留，超预算的旧消息丢弃。"""
        limit = self.limit_for("history")
        kept: list[Any] = []
        used = 0
        for msg in reversed(messages or []):
            content = str(getattr(msg, "content", "") or "")
            tokens = count_tokens(content)
            if used + tokens > limit and kept:
                break
            kept.append(msg)
            used += tokens
        kept.reverse()
        block = ContextBlock(
            name="history",
            content=f"{len(kept)}/{len(messages or [])} 条消息",
            tokens=used,
            truncated=len(kept) < len(messages or []),
        )
        return kept, block
