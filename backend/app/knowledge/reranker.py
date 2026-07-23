"""app/knowledge/reranker.py — 重排序器"""

from typing import Any


class Reranker:
    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = model

    def rerank(self, query: str, documents: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        return documents[:top_k]