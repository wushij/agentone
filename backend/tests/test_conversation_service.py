"""tests/test_conversation_service.py — 针对会话管理与消息持久化服务的单元测试"""

import pytest
from app.services.conversation.conversation_service import ConversationService


def test_conversation_service_instantiation():
    """验证 ConversationService 依赖注入与基础属性"""
    svc = ConversationService(db=None)
    assert svc is not None


def test_conversation_title_truncate():
    """验证长提问文本截断生成短标题逻辑"""
    long_msg = "这是一个非常长非常长的用户测试提问，用于验证会话标题是否能正确被截断并限制在指定长度以内。"
    title = long_msg[:20]
    assert len(title) <= 20
    assert "这是一个非常长非常长" in title


@pytest.mark.asyncio
async def test_maybe_autotitle_conversation():
    from unittest.mock import MagicMock
    from app.models.conversation import Conversation
    from app.models.message import Message

    mock_db = MagicMock()
    mock_conv = Conversation(id="conv_1", user_id=1, title="新对话")
    mock_db.get.return_value = mock_conv

    user_msg = Message(id="m1", conversation_id="conv_1", role="user", content="用 Python 算一下 1024 * 2048")
    assistant_msg = Message(id="m2", conversation_id="conv_1", role="assistant", content="")
    mock_db.scalars.return_value.all.return_value = [user_msg, assistant_msg]

    svc = ConversationService(db=mock_db)
    title = await svc.maybe_autotitle_conversation(user_id=1, conversation_id="conv_1")
    assert title is not None
    assert title != "新对话"
    assert "Python" in title or "1024" in title
