"""app/knowledge/retrievers/hybrid.py — 混合检索器"""

from typing import Any

from app.knowledge.retrieval.retrievers.vector import VectorRetriever


class HybridRetriever(VectorRetriever):
    def __init__(self, store: Any = None, embedder: Any = None, top_k: int = 5, bm25_weight: float = 0.3):
        super().__init__(store=store, embedder=embedder, top_k=top_k)
        self.bm25_weight = bm25_weight

    async def retrieve(self, query: str, kb_ids: list[str] | None = None) -> list[dict[str, Any]]:
        return await super().retrieve(query, kb_ids)