"""app/knowledge/stores/milvus.py — 预留适配器（生产向量库见 RagService JSON store）"""

from typing import Any


class MilvusStore:
    """未启用。生产检索走 app.services.rag_service.RagService。"""

    def __init__(self, collection_name: str = "agentone", host: str = "localhost", port: int = 19530):
        self.collection_name = collection_name
        self.host = host
        self.port = port

    async def add(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> None:
        raise NotImplementedError("MilvusStore 未接入；请使用 RagService")

    async def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError("MilvusStore 未接入；请使用 RagService")

    async def delete(self, ids: list[str]) -> None:
        raise NotImplementedError("MilvusStore 未接入；请使用 RagService")
