"""app/core/engine/checkpointer.py — Checkpointer 策略管理"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver


def create_checkpointer():
    """返回异步全兼容的 Checkpointer 实例。"""
    return MemorySaver()
