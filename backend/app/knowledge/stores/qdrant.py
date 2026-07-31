"""app/knowledge/stores/qdrant.py — Qdrant 向量库适配器（§8.1）

生产级向量后端。opt-in：设置 QDRANT_URL 后由 vector_backend 选用；
未配置或 qdrant-client 未安装时，检索链路继续使用 RagService 的 JSON 存储（回退）。
"""

from __future__ import annotations

from typing import Any

from app.utils.logger import logger

_COLLECTION = "agentone_chunks"
_DIM = 1536


class QdrantStore:
    def __init__(self, url: str, collection: str = _COLLECTION, dim: int = _DIM):
        self.url = url
        self.collection = collection
        self.dim = dim
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        if self.url.startswith("http://") or self.url.startswith("https://"):
            client = QdrantClient(url=self.url)
        elif self.url == ":memory:":
            client = QdrantClient(location=":memory:")
        else:
            client = QdrantClient(path=self.url)
        existing = {c.name for c in client.get_collections().collections}
        if self.collection not in existing:
            client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
        self._client = client
        return client

    async def upsert(self, points: list[dict[str, Any]]) -> None:
        """points: [{id:int, vector:list, payload:{kbId,fileId,fileName,text}}]"""
        from qdrant_client.models import PointStruct

        client = self._get_client()
        client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"]) for p in points],
        )

    async def search(self, kb_id: str, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        client = self._get_client()
        flt = Filter(must=[FieldCondition(key="kbId", match=MatchValue(value=kb_id))])
        # qdrant-client 1.x 已将 search() 替换为 query_points()；兼容旧版 search() 回退
        try:
            resp = client.query_points(
                collection_name=self.collection,
                query=query_vector,
                query_filter=flt,
                limit=top_k,
                with_payload=True,
            )
            hits = getattr(resp, "points", resp)
        except AttributeError:
            hits = client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                query_filter=flt,
                limit=top_k,
            )
        results = []
        for h in hits:
            payload = getattr(h, "payload", None) or {}
            results.append({
                "text": payload.get("text", ""),
                "score": float(getattr(h, "score", 0.0)),
                "fileName": payload.get("fileName", ""),
                "fileId": payload.get("fileId", ""),
                "kbId": payload.get("kbId", ""),
            })
        return results

    async def delete_by_kb(self, kb_id: str) -> None:
        from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

        client = self._get_client()
        client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="kbId", match=MatchValue(value=kb_id))])
            ),
        )


_store: QdrantStore | None = None
_checked = False


def get_qdrant_store() -> QdrantStore | None:
    """返回已配置且可用的 QdrantStore；未配置/不可用返回 None（触发 JSON 回退）。"""
    global _store, _checked
    if _checked:
        return _store
    _checked = True
    try:
        from app.config.settings import get_settings

        url = getattr(get_settings(), "QDRANT_URL", "") or ""
        if not url:
            return None
        import qdrant_client  # noqa: F401

        _store = QdrantStore(url)
        _store._get_client()  # 触发连接与建集合
        logger.info(f"[Qdrant] 已启用向量后端: {url}")
    except Exception as exc:
        logger.warning(f"[Qdrant] 不可用，回退 JSON 向量存储: {exc}")
        _store = None
    return _store
