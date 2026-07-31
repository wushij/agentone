"""tests/test_cost_service.py — 针对成本中心（CostManager）与 Token 价格计算的单元测试"""

import pytest
from app.runtime.cost import get_cost_manager
from app.runtime.cost.manager import CostManager, compute_cost


def test_compute_cost():
    """验证根据 Provider 与 Token 数量计算 USD 成本"""
    # 测试 openai 规则 (假设 prompt $0.15/1M, completion $0.6/1M)
    cost = compute_cost("openai", prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert cost > 0.0


def test_cost_manager_singleton():
    """验证 CostManager 获取与结构"""
    mgr = get_cost_manager()
    assert mgr is not None
    assert isinstance(mgr, CostManager)
