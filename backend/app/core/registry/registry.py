"""app/core/registry.py — Agent/Skill/Tool 注册中心"""

from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.compute.calculator import CalculatorTool
from app.tools.database.database import DatabaseTool
from app.tools.file.file import FileTool
from app.tools.network.search import SearchTool

_TOOLS: dict[str, BaseTool] = {
    CalculatorTool.name: CalculatorTool(),
    SearchTool.name: SearchTool(),
    FileTool.name: FileTool(),
    DatabaseTool.name: DatabaseTool(),
}


def is_tool_enabled(name: str) -> bool:
    try:
        from app.db.session import SessionLocal
        from app.services.tool.tool_service import ToolService

        db = SessionLocal()
        try:
            return ToolService(db).is_enabled(name)
        finally:
            db.close()
    except Exception:
        return True


def get_tool(name: str) -> BaseTool | None:
    return _TOOLS.get(name)


def list_tools() -> list[str]:
    return list(_TOOLS.keys())


def list_builtin_tools() -> list[BaseTool]:
    return list(_TOOLS.values())


def list_tool_infos() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "status": "enabled" if is_tool_enabled(tool.name) else "disabled",
        }
        for tool in _TOOLS.values()
    ]