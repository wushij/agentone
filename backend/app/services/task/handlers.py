"""app/services/task/handlers.py — 默认异步任务处理器（§14）

agent 任务：后台跑 Agent Runtime 完成"超出一次 HTTP 连接"的复合任务，
中途经 push 回报进度，完成后把最终回答登记为 Markdown Artifact 并作为结果返回。
"""

from __future__ import annotations

import uuid

from app.runtime.scheduler.scheduler import ProgressPush


async def run_agent_task(task_id: str, user_id: int, input_text: str, push: ProgressPush) -> str:
    """执行一个长 Agent 任务并返回最终文本结果。"""
    await push(15, "初始化 Agent Runtime")

    from app.runtime import get_runtime

    runtime = get_runtime()
    thread_id = f"task_{task_id}"

    await push(35, "自主规划与工具执行中")
    result_state = await runtime.invoke(
        input_text,
        session_id=thread_id,
        user_id=str(user_id),
        conversation_id=thread_id,
    )
    answer = result_state.get("final_answer") or result_state.get("llm_response") or ""

    await push(85, "整理产出物")
    # 最终报告登记为 Markdown Artifact，供前端 Artifact 面板 / 任务详情展示
    try:
        from app.runtime.artifacts import get_artifact_manager

        get_artifact_manager().register(
            user_id=user_id,
            type="markdown",
            title=f"任务报告 · {input_text[:40]}",
            content=answer or "(无内容)",
            task_id=task_id,
            message_id=uuid.uuid4().hex,
        )
    except Exception:
        pass

    await push(95, "生成通知")
    # 站内通知：任务完成
    try:
        from app.services.system.notify_hub import get_notify_hub

        hub = await get_notify_hub()
        await hub.publish(user_id, {
            "type": "notification",
            "payload": {
                "level": "success",
                "title": "任务完成",
                "body": f"「{input_text[:30]}」已执行完毕，产出报告已生成。",
                "action": {"label": "查看任务", "route": "/tasks"},
            },
        })
    except Exception:
        pass

    return answer or "(任务完成，但无文本输出)"
