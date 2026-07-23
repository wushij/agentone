"""app/knowledge/retrievers/vector.py — 向量检索器"""

from typing import Any


class VectorRetriever:
    def __init__(self, store: Any = None, embedder: Any = None, top_k: int = 5):
        self.store = store
        self.embedder = embedder
        self.top_k = top_k

    async def retrieve(self, query: str, kb_ids: list[str] | None = None) -> list[dict[str, Any]]:
        return []

    async def add_documents(self, documents: list[dict[str, Any]], kb_id: str) -> None:
        pass