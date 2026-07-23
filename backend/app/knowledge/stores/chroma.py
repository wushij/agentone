"""app/knowledge/stores/chroma.py — 预留适配器（生产向量库见 RagService JSON store）"""

from typing import Any


class ChromaStore:
    """未启用。生产检索走 app.services.rag_service.RagService。"""

    def __init__(self, collection_name: str = "agentone", persist_directory: str = ""):
        self.collection_name = collection_name
        self.persist_directory = persist_directory

    async def add(self, vectors: list[list[float]], metadata: list[dict[str, Any]]) -> None:
        raise NotImplementedError("ChromaStore 未接入；请使用 RagService")

    async def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError("ChromaStore 未接入；请使用 RagService")

    async def delete(self, ids: list[str]) -> None:
        raise NotImplementedError("ChromaStore 未接入；请使用 RagService")
