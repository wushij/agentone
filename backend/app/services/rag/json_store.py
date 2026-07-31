"""app/services/rag/json_store.py — 本地 JSON 物理向量库持久化与缓存失效"""

from __future__ import annotations

import json
from app.storage import data_root, vector_store_json


def load_vector_store() -> dict:
    path = vector_store_json()
    if not path.exists():
        return {"chunks": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"chunks": []}


def save_vector_store(store: dict):
    data_root()
    path = vector_store_json()
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


async def invalidate_rag_cache(kb_id: str) -> None:
    """主动失效（§8.3）：文档变更后 bump 该库版本。"""
    try:
        from app.cache import RagCache

        await RagCache().bump_version(kb_id)
    except Exception:
        pass


def invalidate_rag_cache_sync(kb_id: str) -> None:
    """同步上下文调用（remove/clear）：尽力失效缓存，不阻断主流程。"""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(invalidate_rag_cache(kb_id))
    except RuntimeError:
        try:
            asyncio.run(invalidate_rag_cache(kb_id))
        except Exception:
            pass
