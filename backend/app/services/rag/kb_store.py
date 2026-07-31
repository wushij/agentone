"""app/services/rag/kb_store.py — 知识库配置仓储（§8.1）

把 KB 元数据从 data/knowledge.json 下沉到 MySQL knowledge_bases 表，
并打断原 rag_service → api.v1.knowledge._load_kb 的循环依赖。

- DB 为唯一真相源；首次加载若表空且存在旧 knowledge.json，自动整体迁移入库；
- DB 不可用时降级读写 JSON，保证任何环境可运行；
- 对外 dict 结构与原 knowledge.json 条目完全兼容（id/name/fileIds/topK/...）。
"""

from __future__ import annotations

import json
from typing import Any

from app.storage import data_root, runtime_json
from app.utils.logger import logger

_CONFIG_KEYS = (
    "fileIds", "chunkSize", "chunkOverlap", "segmentDelimiter",
    "embeddingModel", "retrievalMode", "topK", "scoreThreshold",
    "queryTransform", "createdAt",
)


def _json_path():
    return runtime_json("knowledge.json")


def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description or "",
        **(row.config or {}),
    }


def _dict_to_config(kb: dict) -> dict:
    return {k: kb[k] for k in _CONFIG_KEYS if k in kb}


def _load_json_file() -> list[dict]:
    path = _json_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_json_file(kb_list: list[dict]) -> None:
    data_root()
    _json_path().write_text(json.dumps(kb_list, ensure_ascii=False, indent=2), encoding="utf-8")


def load_all() -> list[dict]:
    """读取全部知识库配置（DB 优先，表空时从 JSON 迁移，DB 不可用降级 JSON）。"""
    try:
        from app.db.session import SessionLocal
        from app.models.knowledge_base import KnowledgeBase

        db = SessionLocal()
        try:
            rows = db.query(KnowledgeBase).all()
            if not rows:
                legacy = _load_json_file()
                if legacy:
                    for kb in legacy:
                        db.merge(KnowledgeBase(
                            id=kb["id"],
                            name=kb.get("name", kb["id"]),
                            description=kb.get("description", ""),
                            config=_dict_to_config(kb),
                        ))
                    db.commit()
                    rows = db.query(KnowledgeBase).all()
                    logger.info(f"[KBStore] 已从 knowledge.json 迁移 {len(rows)} 个知识库入库")
            return [_row_to_dict(r) for r in rows]
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"[KBStore] DB 不可用，降级读 JSON: {exc}")
        return _load_json_file()


def get_kb(kb_id: str) -> dict | None:
    return next((k for k in load_all() if k["id"] == kb_id), None)


def save_all(kb_list: list[dict]) -> None:
    """全量落库（upsert + 删除多余），DB 不可用降级写 JSON。"""
    try:
        from app.db.session import SessionLocal
        from app.models.knowledge_base import KnowledgeBase

        db = SessionLocal()
        try:
            incoming_ids = {kb["id"] for kb in kb_list}
            for kb in kb_list:
                db.merge(KnowledgeBase(
                    id=kb["id"],
                    name=kb.get("name", kb["id"]),
                    description=kb.get("description", ""),
                    config=_dict_to_config(kb),
                ))
            for row in db.query(KnowledgeBase).all():
                if row.id not in incoming_ids:
                    db.delete(row)
            db.commit()
            return
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"[KBStore] DB 不可用，降级写 JSON: {exc}")
        _save_json_file(kb_list)
