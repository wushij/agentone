"""app/runtime/artifacts/manager.py — Artifact Manager（§12.2）

统一产物注册与读取：工具产出（chart 的 ECharts JSON、python_executor 的图表/文件、
code 生成物）经此登记为 Artifact，落库后由 SSE `artifact` 事件通知前端面板。
"""

from __future__ import annotations

from typing import Any

from app.utils.logger import logger

ARTIFACT_TYPES = {
    "markdown", "html", "code", "image", "csv", "excel", "pdf", "mermaid", "chart",
}


class ArtifactManager:
    def register(
        self,
        *,
        user_id: int | None,
        type: str,
        title: str = "",
        content: str = "",
        language: str | None = None,
        conversation_id: str | None = None,
        message_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any] | None:
        """登记一个产物，返回其精简 dict（供 SSE 事件 / API）。DB 不可用返回 None。"""
        art_type = type if type in ARTIFACT_TYPES else "markdown"
        try:
            from app.db.session import SessionLocal
            from app.models.artifact import Artifact

            db = SessionLocal()
            try:
                row = Artifact(
                    user_id=user_id or 0,
                    type=art_type,
                    title=title or art_type,
                    content=content or "",
                    language=language,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    task_id=task_id,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return self._to_dict(row)
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"[Artifact] 登记失败（已降级跳过）: {exc}")
            return None

    def list_by_conversation(self, user_id: int, conversation_id: str) -> list[dict]:
        return self._query(user_id, conversation_id=conversation_id)

    def list_by_task(self, user_id: int, task_id: str) -> list[dict]:
        return self._query(user_id, task_id=task_id)

    def get(self, user_id: int, artifact_id: str) -> dict | None:
        try:
            from app.db.session import SessionLocal
            from app.models.artifact import Artifact

            db = SessionLocal()
            try:
                row = db.query(Artifact).filter(
                    Artifact.id == artifact_id, Artifact.user_id == user_id
                ).first()
                return self._to_dict(row) if row else None
            finally:
                db.close()
        except Exception:
            return None

    def _query(self, user_id: int, **filters) -> list[dict]:
        try:
            from app.db.session import SessionLocal
            from app.models.artifact import Artifact

            db = SessionLocal()
            try:
                q = db.query(Artifact).filter(Artifact.user_id == user_id)
                for key, value in filters.items():
                    q = q.filter(getattr(Artifact, key) == value)
                rows = q.order_by(Artifact.created_at.desc()).all()
                return [self._to_dict(r) for r in rows]
            finally:
                db.close()
        except Exception:
            return []

    @staticmethod
    def _to_dict(row) -> dict:
        return {
            "id": row.id,
            "type": row.type,
            "title": row.title,
            "content": row.content,
            "language": row.language,
            "conversationId": row.conversation_id,
            "messageId": row.message_id,
            "taskId": row.task_id,
            "version": row.version,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        }


_manager: ArtifactManager | None = None


def get_artifact_manager() -> ArtifactManager:
    global _manager
    if _manager is None:
        _manager = ArtifactManager()
    return _manager
