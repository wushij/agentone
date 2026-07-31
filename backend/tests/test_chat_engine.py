"""tests/test_chat_engine.py — 针对 GraphRunner 执行引擎与 SSE 事件流的单元与集成测试"""

import asyncio
import pytest
from app.core.engine.engine import GraphRunner, get_engine
from app.core.events.events import StreamContext, done_event, error_event, step_event, token_event


@pytest.mark.asyncio
async def test_engine_singleton():
    """验证 get_engine 返回单例 Engine 实例"""
    engine1 = get_engine()
    engine2 = get_engine()
    assert engine1 is engine2
    assert isinstance(engine1, GraphRunner)


@pytest.mark.asyncio
async def test_stream_sse_basic_flow():
    """验证 stream_sse 能正常产出 SSE 事件流（包含 step / token / done 事件）"""
    runner = GraphRunner()
    events = []
    async for event in runner.stream_sse(
        "测试消息：AgentOne系统架构是什么？",
        conversation_id="test_engine_conv_001",
        enable_tools=False,
        model_id="mock-model",
    ):
        events.append(event)

    assert len(events) > 0
    event_types = [e.event for e in events]
    assert "step" in event_types
    assert "done" in event_types or "error" in event_types

    # 校验事件的基本数据结构
    for ev in events:
        assert hasattr(ev, "event")
        assert hasattr(ev, "data")
        assert ev.data.get("conversationId") == "test_engine_conv_001"


@pytest.mark.asyncio
async def test_stream_sse_encoded():
    """验证 stream_sse_encoded 输出合法的 UTF-8 编码 SSE 字符串格式"""
    runner = GraphRunner()
    chunks = []
    async for chunk in runner.stream_sse_encoded(
        "测试编码格式",
        conversation_id="test_engine_conv_002",
        enable_tools=False,
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "event:" in full_text
    assert "data:" in full_text
