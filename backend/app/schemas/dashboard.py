"""app/schemas/dashboard.py — 大盘与统计 Pydantic Schema"""

from pydantic import BaseModel


class DashboardStatsOut(BaseModel):
    user_count: int
    conversation_count: int
    message_count: int
    token_cost_total: float
