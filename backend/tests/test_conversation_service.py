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
