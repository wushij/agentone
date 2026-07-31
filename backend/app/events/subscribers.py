"""app/events/subscribers.py — 领域事件订阅方（§11）

把原先散落在 engine 里的内联副作用改为订阅 EventBus 领域事件：
- ToolEnd / ToolFailed → 写 ToolLog（工具审计不再与执行逻辑耦合）
- CostRecorded 等其余消费方（Cost/Evaluator）后续在此扩展

register_subscribers() 在应用启动时调用一次（幂等）。
"""

from __future__ import annotations

from app.events.bus import event_bus
from app.events.message import EventMessage
from app.utils.logger import logger

_registered = False


async def _on_tool_event(event: EventMessage) -> None:
    """ToolManager 发出的 ToolEnd/ToolFailed → 落 ToolLog。"""
    data = event.data or {}
    tool_name = str(data.get("tool") or "")
    if not tool_name:
        return
    try:
        import json

        from app.db.session import SessionLocal
        from app.models.tool_log import ToolLog

        db = SessionLocal()
        try:
            db.add(ToolLog(
                user_id=int(data["userId"]) if data.get("userId") else None,
                conversation_id=data.get("conversationId"),
                tool_name=tool_name,
                params=json.dumps(data.get("arguments") or {}, ensure_ascii=False),
                result=(data.get("error") or data.get("output") or "")[:4000] or None,
                duration_ms=int(data.get("durationMs") or 0),
                status="error" if data.get("error") else "success",
            ))
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"[Subscribers] ToolLog 写入失败: {exc}")


async def _on_agent_status_audit(event: EventMessage) -> None:
    """AgentStatus → 写 AuditLog（仅 success/error 终态，与原内联行为一致）。"""
    data = event.data or {}
    status = str(data.get("status") or "")
    user_id = data.get("userId")
    if status not in ("success", "error") or not user_id:
        return
    try:
        from app.db.session import SessionLocal
        from app.services.system.audit_log_service import AuditLogService

        db = SessionLocal()
        try:
            node = str(data.get("node") or "")
            label_map = {
                "planner": "任务规划器",
                "researcher": "意图与上下文分析器",
                "tool": "Agent 工具节点",
                "reviewer": "回答质量审核员",
                "unsupported": "未支持模式处理",
                "error_handler": "异常降级处理",
            }
            node_label = label_map.get(node, node)
            detail_content = str(data.get("detail") or data.get("tool") or "").strip()
            if not detail_content or detail_content == node:
                if node == "reviewer":
                    detail_content = "完成最终回答风控与质量审核，校验符合交付标准"
                elif node == "planner":
                    detail_content = "分析用户输入，拆解生成 Agent 执行步骤与拓扑图"
                elif node == "researcher":
                    detail_content = "检索知识库上下文并完成意图路由分发"
                elif node == "tool":
                    detail_content = "调用底层关联工具完成功能计算"
                else:
                    detail_content = f"完成 {node_label} 阶段执行"

            AuditLogService(db).write(
                user_id=int(user_id),
                module="agent",
                action=f"{node}:{status}",
                detail=f"【{node_label}】{detail_content}",
                status="success" if status == "success" else "error",
            )
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"[Subscribers] AuditLog 写入失败: {exc}")


async def _on_agent_status_notify(event: EventMessage) -> None:
    """AgentStatus → WS 推送（agent_status 主题，驱动前端实时步骤面板）。"""
    data = event.data or {}
    user_id = data.get("userId")
    if not user_id:
        return
    try:
        from app.services.system.notify_hub import get_notify_hub

        hub = await get_notify_hub()
        await hub.publish(
            int(user_id),
            {
                "type": "agent_status",
                "payload": {
                    "conversationId": data.get("conversationId"),
                    "node": data.get("node"),
                    "status": data.get("status"),
                    "tool": data.get("tool"),
                    "elapsedMs": data.get("elapsedMs"),
                    "error": data.get("error"),
                    "detail": data.get("detail"),
                    "label": data.get("label"),
                },
            },
        )
    except Exception as exc:
        logger.warning(f"[Subscribers] AgentStatus WS 推送失败: {exc}")


def register_subscribers() -> None:
    global _registered
    if _registered:
        return
    event_bus.subscribe("ToolEnd", _on_tool_event)
    event_bus.subscribe("ToolFailed", _on_tool_event)
    event_bus.subscribe("AgentStatus", _on_agent_status_audit)
    event_bus.subscribe("AgentStatus", _on_agent_status_notify)
    _registered = True
    logger.info("[Subscribers] 领域事件订阅已注册（ToolEnd/ToolFailed→ToolLog；AgentStatus→Audit+Notify）")
