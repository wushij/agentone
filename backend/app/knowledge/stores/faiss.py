"""app/knowledge/stores/faiss.py — 预留适配器（生产向量库见 RagService JSON store）"""

from typing import Any


class FaissStore:
    """未启用。生产检索走 app.services.rag_service.RagService。"""

    def __init__(self, index_path: str = ""):
        self.index_path = index_path

    async def add(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> None:
        raise NotImplementedError("FaissStore 未接入；请使用 RagService")

    async def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError("FaissStore 未接入；请使用 RagService")

    async def delete(self, ids: list[str]) -> None:
        raise NotImplementedError("FaissStore 未接入；请使用 RagService")
