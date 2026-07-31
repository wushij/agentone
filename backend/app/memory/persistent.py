"""app/memory/persistent.py — 持久记忆服务（§7）

- memories 表落库：重启不丢、跨会话可用
- 真向量检索：embedding 余弦相似度（替换关键词匹配）
- 融合排序：importance × recency_decay × relevance
- 自动提取：LLM 从对话轮提取事实/偏好，相似度 > 0.92 合并去重
- 遗忘机制：低 importance + 长期未访问 → 衰减，衰减至阈值以下删除（置顶免疫）
"""

from __future__ import annotations

import asyncio
import json
import math
import re
from datetime import datetime, timedelta
from typing import Any

from app.utils.logger import logger

DEDUP_SIMILARITY = 0.92
RECENCY_HALF_LIFE_DAYS = 30.0  # 30 天权重减半
DECAY_IDLE_DAYS = 30  # 超过 30 天未访问才衰减
DECAY_FACTOR = 0.8
DELETE_THRESHOLD = 0.05


def _cosine(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def _recency_decay(last_time: datetime | None) -> float:
    if last_time is None:
        return 1.0
    days = max(0.0, (datetime.now() - last_time).total_seconds() / 86400)
    return 0.5 ** (days / RECENCY_HALF_LIFE_DAYS)


async def _embed(text: str) -> list[float]:
    """用默认模型凭据做 embedding（复用 EmbeddingCache）。"""
    from app.db.session import SessionLocal
    from app.services.llm.model_service import ModelService
    from app.services.rag.rag_service import get_embedding

    api_key = base_url = None
    model_name = "text-embedding-3-small"
    try:
        db = SessionLocal()
        try:
            row = ModelService(db).get_default()
            if row:
                api_key, base_url, model_name = row.api_key, row.base_url, row.model_name
        finally:
            db.close()
    except Exception:
        pass
    return await get_embedding(text, api_key, base_url, model_name)


class PersistentMemoryService:
    """memories 表的读写门面；DB 不可用时静默降级为 no-op，不阻断主链路。"""

    # ---------- 写入 ----------

    async def add(
        self,
        user_id: int,
        content: str,
        *,
        kind: str = "fact",
        scope: str = "user",
        importance: float = 0.5,
    ) -> int | None:
        content = content.strip()
        if not content or len(content) > 2000:
            return None
        try:
            vector = await _embed(content)
            from app.db.session import SessionLocal
            from app.models.memory import MemoryEntry

            db = SessionLocal()
            try:
                # 向量去重：与现有记忆相似度 > 0.92 → merge（提升 importance，不新增）
                rows = db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).all()
                for row in rows:
                    if row.embedding and _cosine(vector, row.embedding) > DEDUP_SIMILARITY:
                        row.importance = min(1.0, max(row.importance, importance) + 0.05)
                        row.access_count += 1
                        row.last_accessed_at = datetime.now()
                        db.commit()
                        return row.id

                entry = MemoryEntry(
                    user_id=user_id,
                    scope=scope,
                    kind=kind,
                    content=content,
                    embedding=vector,
                    importance=max(0.0, min(1.0, importance)),
                )
                db.add(entry)
                db.commit()
                db.refresh(entry)
                await self._publish("MemoryWrite", {"userId": user_id, "kind": kind, "memoryId": entry.id})
                return entry.id
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"[Memory] 写入失败（已降级跳过）: {exc}")
            return None

    # ---------- 检索（融合排序） ----------

    async def search(self, user_id: int, query: str, *, top_k: int = 5) -> list[dict[str, Any]]:
        try:
            query_vector = await _embed(query) if query else None
            from app.db.session import SessionLocal
            from app.models.memory import MemoryEntry

            db = SessionLocal()
            try:
                rows = db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).all()
                scored: list[tuple[float, MemoryEntry]] = []
                for row in rows:
                    relevance = (
                        _cosine(query_vector, row.embedding)
                        if query_vector and row.embedding
                        else 0.3
                    )
                    recency = _recency_decay(row.last_accessed_at or row.created_at)
                    boost = 1.5 if row.pinned else 1.0
                    score = row.importance * (0.3 + 0.7 * recency) * (0.3 + 0.7 * relevance) * boost
                    scored.append((score, row))
                scored.sort(key=lambda x: x[0], reverse=True)

                hits = scored[:top_k]
                now = datetime.now()
                for _, row in hits:
                    row.access_count += 1
                    row.last_accessed_at = now
                db.commit()

                await self._publish("MemoryRecall", {"userId": user_id, "count": len(hits)})
                return [
                    {
                        "id": row.id,
                        "content": row.content,
                        "kind": row.kind,
                        "importance": row.importance,
                        "score": round(score, 4),
                    }
                    for score, row in hits
                ]
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"[Memory] 检索失败（已降级为空）: {exc}")
            return []

    # ---------- 用户可见可控（§7.2 合规刚需） ----------

    def list_memories(self, user_id: int, *, page: int = 1, size: int = 20) -> tuple[list[dict], int]:
        from app.db.session import SessionLocal
        from app.models.memory import MemoryEntry

        db = SessionLocal()
        try:
            base = db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id)
            total = base.count()
            rows = (
                base.order_by(MemoryEntry.pinned.desc(), MemoryEntry.importance.desc(), MemoryEntry.id.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "content": r.content,
                    "kind": r.kind,
                    "scope": r.scope,
                    "importance": round(r.importance, 3),
                    "accessCount": r.access_count,
                    "pinned": bool(r.pinned),
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ], total
        finally:
            db.close()

    def delete_memory(self, user_id: int, memory_id: int) -> bool:
        from app.db.session import SessionLocal
        from app.models.memory import MemoryEntry

        db = SessionLocal()
        try:
            row = db.query(MemoryEntry).filter(
                MemoryEntry.id == memory_id, MemoryEntry.user_id == user_id
            ).first()
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()

    def set_pinned(self, user_id: int, memory_id: int, pinned: bool) -> bool:
        from app.db.session import SessionLocal
        from app.models.memory import MemoryEntry

        db = SessionLocal()
        try:
            row = db.query(MemoryEntry).filter(
                MemoryEntry.id == memory_id, MemoryEntry.user_id == user_id
            ).first()
            if row is None:
                return False
            row.pinned = 1 if pinned else 0
            if pinned:
                row.importance = min(1.0, row.importance + 0.1)
            db.commit()
            return True
        finally:
            db.close()

    # ---------- 自动提取（§7.2） ----------

    async def extract_from_turn(self, user_id: int, user_text: str, assistant_text: str = "") -> int:
        """LLM 从对话轮提取值得长期记住的事实/偏好并落库；返回写入条数。"""
        if not user_text.strip():
            return 0
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            from app.llm.factory import create_chat_model

            llm = create_chat_model()
            dialogue = f"用户: {user_text}"
            if assistant_text:
                dialogue += f"\n助手: {assistant_text[:1000]}"
            response = await llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "从对话中提取值得长期记住的用户事实或偏好（如姓名、职业、喜好、项目背景、明确要求）。"
                            "只输出 JSON 数组，每项 {\"content\": \"事实描述\", \"kind\": \"fact|preference\", "
                            "\"importance\": 0.0到1.0}；没有值得记的输出 []。不要输出其他内容。"
                        )
                    ),
                    HumanMessage(content=dialogue),
                ]
            )
            text = response.content if isinstance(response.content, str) else str(response.content)
            match = re.search(r"\[[\s\S]*\]", text)
            if not match:
                return 0
            items = json.loads(match.group(0))
            written = 0
            for item in items[:5]:
                if not isinstance(item, dict):
                    continue
                content = str(item.get("content") or "").strip()
                if len(content) < 4:
                    continue
                kind = item.get("kind") if item.get("kind") in ("fact", "preference", "episode", "skill") else "fact"
                importance = float(item.get("importance", 0.5))
                if await self.add(user_id, content, kind=kind, importance=importance) is not None:
                    written += 1
            return written
        except Exception as exc:
            logger.warning(f"[Memory] 自动提取失败（跳过）: {exc}")
            return 0

    def schedule_extract(self, user_id: int, user_text: str, assistant_text: str = "") -> None:
        """fire-and-forget 后台提取，不阻塞响应流。"""
        try:
            asyncio.get_running_loop().create_task(
                self.extract_from_turn(user_id, user_text, assistant_text)
            )
        except RuntimeError:
            pass

    # ---------- 遗忘机制（§7.2） ----------

    def decay(self) -> dict[str, int]:
        """低 importance + 长期未访问的记忆衰减；衰减至阈值以下删除（置顶免疫）。"""
        from app.db.session import SessionLocal
        from app.models.memory import MemoryEntry

        decayed = removed = 0
        cutoff = datetime.now() - timedelta(days=DECAY_IDLE_DAYS)
        try:
            db = SessionLocal()
            try:
                rows = db.query(MemoryEntry).filter(MemoryEntry.pinned == 0).all()
                for row in rows:
                    last = row.last_accessed_at or row.created_at
                    if last and last > cutoff:
                        continue
                    row.importance = row.importance * DECAY_FACTOR
                    decayed += 1
                    if row.importance < DELETE_THRESHOLD:
                        db.delete(row)
                        removed += 1
                # 过期记忆清理
                expired = db.query(MemoryEntry).filter(
                    MemoryEntry.expires_at.isnot(None), MemoryEntry.expires_at < datetime.now()
                ).all()
                for row in expired:
                    db.delete(row)
                    removed += 1
                db.commit()
            finally:
                db.close()
        except Exception as exc:
            logger.warning(f"[Memory] 遗忘任务失败: {exc}")
        return {"decayed": decayed, "removed": removed}

    # ---------- 事件 ----------

    async def _publish(self, event_type: str, payload: dict) -> None:
        try:
            from app.events.bus import event_bus
            from app.events.message import EventMessage

            await event_bus.publish(EventMessage(event_type=event_type, data=payload, sender="memory"))
        except Exception:
            pass


_persistent: PersistentMemoryService | None = None


def get_persistent_memory() -> PersistentMemoryService:
    global _persistent
    if _persistent is None:
        _persistent = PersistentMemoryService()
    return _persistent
