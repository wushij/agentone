"""backend/app/graph/nodes/tool_node.py"""

from __future__ import annotations

import json

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.graph.state import AgentState
from app.models.tool_log import ToolLog
from app.tools.registry import get_tool, is_tool_enabled


def _write_tool_log(
    state: AgentState,
    *,
    tool_name: str,
    params: dict,
    result: str,
    duration_ms: int,
    status: str,
) -> None:
    user_id = state.get("user_id")
    if not user_id:
        return
    db = SessionLocal()
    try:
        db.add(
            ToolLog(
                user_id=int(user_id),
                conversation_id=state.get("conversation_id"),
                tool_name=tool_name,
                params=json.dumps(params, ensure_ascii=False),
                result=result[:4000] if result else None,
                duration_ms=duration_ms,
                status=status,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


async def tool_node(state: AgentState) -> dict:
    tool_name = state.get("tool_name") or ""
    tool_input = state.get("tool_input") or {}
    retries = state.get("tool_retries") or 0

    tool = get_tool(tool_name)
    if tool is None:
        return {
            "tool_error": f"工具未注册: {tool_name}",
            "error": f"工具未注册: {tool_name}",
            "current_node": "tool",
        }
    if not is_tool_enabled(tool_name):
        return {
            "tool_error": f"工具已禁用: {tool_name}",
            "error": f"工具已禁用: {tool_name}",
            "current_node": "tool",
        }

    result = await tool.run(
        **tool_input,
        _user_id=state.get("user_id"),
        _conversation_id=state.get("conversation_id"),
    )
    if result.error:
        max_retries = get_settings().TOOL_MAX_RETRIES
        if retries < max_retries:
            return {
                "tool_error": result.error,
                "tool_retries": retries + 1,
                "current_node": "tool",
                "metadata": {"tool_retry": retries + 1},
            }
        _write_tool_log(
            state,
            tool_name=tool_name,
            params=tool_input,
            result=result.error,
            duration_ms=result.duration_ms,
            status="error",
        )
        return {
            "tool_error": result.error,
            "error": result.error,
            "current_node": "tool",
            "metadata": {"tool_duration_ms": result.duration_ms},
        }

    _write_tool_log(
        state,
        tool_name=tool_name,
        params=tool_input,
        result=result.output,
        duration_ms=result.duration_ms,
        status="success",
    )
    return {
        "tool_result": result.output,
        "tool_error": "",
        "current_node": "tool",
        "metadata": {"tool_duration_ms": result.duration_ms},
    }
