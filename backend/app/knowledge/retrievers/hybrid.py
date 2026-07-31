"""app/knowledge/retrievers/hybrid.py — 混合检索器

修复坏 import 死代码（原 import 了不存在的 app.knowledge.retrieval.* 路径）。
当前混合打分由 RagService._blend_retrieval_score 按知识库 retrievalMode 完成
（词法分 + 余弦分）；真 BM25 + RRF 融合见路线图第二组 B 线。
"""

from typing import Any

from app.knowledge.retrievers.vector import VectorRetriever


class HybridRetriever(VectorRetriever):
    def __init__(self, store: Any = None, embedder: Any = None, top_k: int = 5, bm25_weight: float = 0.3):
        super().__init__(store=store, embedder=embedder, top_k=top_k)
        self.bm25_weight = bm25_weight

    async def retrieve(self, query: str, kb_ids: list[str] | None = None, top_k: int | None = None) -> list[dict[str, Any]]:
        return await super().retrieve(query, kb_ids, top_k=top_k)
