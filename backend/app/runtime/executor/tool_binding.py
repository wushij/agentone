"""app/runtime/executor/tool_binding.py — Function Calling 绑定层（§3.1）

利用 BaseTool.to_function_schema() 通过 llm.bind_tools() 让模型自主决定
调用哪个工具、带什么参数；模型不支持 FC（如 Mock）时返回 None，
由调用方回退到 detect_intent 规则路径。
"""

from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool
from app.utils.logger import logger


def bind_tools_if_supported(llm: Any, tools: list[BaseTool]) -> Any | None:
    """尝试把工具 Schema 绑定到模型；不支持 FC 返回 None（触发规则回退）。"""
    if not tools:
        return None
    schemas = [t.to_function_schema() for t in tools]
    try:
        return llm.bind_tools(schemas)
    except (NotImplementedError, AttributeError):
        return None
    except Exception as exc:
        logger.warning(f"[ToolBinding] bind_tools 失败，回退规则意图: {exc}")
        return None


def extract_tool_calls(message: Any) -> list[dict[str, Any]]:
    """从 AIMessage 提取标准化 tool_calls：[{id, name, args}]。"""
    calls = getattr(message, "tool_calls", None) or []
    normalized: list[dict[str, Any]] = []
    for call in calls:
        if isinstance(call, dict):
            normalized.append(
                {
                    "id": str(call.get("id") or f"call_{len(normalized)}"),
                    "name": str(call.get("name") or ""),
                    "args": dict(call.get("args") or {}),
                }
            )
    return normalized


def accumulate_usage(message: Any, totals: dict[str, int]) -> None:
    """把 AIMessage.usage_metadata 累加进 totals（真实 token 透传，§9.2）。"""
    usage = getattr(message, "usage_metadata", None)
    if usage:
        totals["prompt_tokens"] = totals.get("prompt_tokens", 0) + int(usage.get("input_tokens") or 0)
        totals["completion_tokens"] = totals.get("completion_tokens", 0) + int(usage.get("output_tokens") or 0)
