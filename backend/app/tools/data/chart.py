"""app/tools/data/chart.py — 图表工具（§4.3）

将数据转为 ECharts option JSON，注册为 chart Artifact，前端面板可交互渲染。
不依赖外部服务，纯本地生成。
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class ChartArgs(BaseModel):
    chart_type: str = Field(default="bar", description="图表类型：bar/line/pie")
    title: str = Field(default="图表", description="图表标题")
    categories: list[str] = Field(default_factory=list, description="X 轴分类（bar/line）或饼图扇区名")
    values: list[float] = Field(default_factory=list, description="对应数值序列")


def _build_option(chart_type: str, title: str, categories: list[str], values: list[float]) -> dict[str, Any]:
    ctype = chart_type if chart_type in ("bar", "line", "pie") else "bar"
    if ctype == "pie":
        data = [{"name": c, "value": v} for c, v in zip(categories, values)]
        return {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 0},
            "series": [{"type": "pie", "radius": "60%", "data": data}],
        }
    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": categories},
        "yAxis": {"type": "value"},
        "series": [{"type": ctype, "data": values}],
    }


class ChartTool(BaseTool):
    name = "chart"
    description = "数据可视化：把分类与数值转为图表（bar/line/pie），生成可交互图表产物"
    args_schema = ChartArgs
    timeout_s = 10.0

    async def run(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        chart_type = str(kwargs.get("chart_type") or "bar")
        title = str(kwargs.get("title") or "图表")
        categories = list(kwargs.get("categories") or [])
        values = [float(v) for v in (kwargs.get("values") or [])]
        if not categories or not values:
            return ToolResult(output="", duration_ms=0, error="缺少 categories 或 values 数据")

        option = _build_option(chart_type, title, categories, values)
        content = json.dumps(option, ensure_ascii=False)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolResult(
            output=f"已生成「{title}」{chart_type} 图表（{len(values)} 个数据点）",
            duration_ms=duration_ms,
            artifact={"type": "chart", "title": title, "content": content},
        )
