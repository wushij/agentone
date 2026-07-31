"""app/knowledge/reranker.py — 重排序器（§8.4 真 Reranker）

优先使用本地 cross-encoder（sentence-transformers）；未安装则降级为
词法重合 + 原始分数的启发式重排，保证任何环境可运行且优于"直接截断"。
"""

from __future__ import annotations

from typing import Any

from app.utils.logger import logger

_model = None
_model_failed = False


def _load_model(model_name: str):
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    try:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(model_name)
        logger.info(f"[Reranker] 已加载 cross-encoder: {model_name}")
    except Exception as exc:
        _model_failed = True
        logger.warning(f"[Reranker] cross-encoder 不可用，降级启发式重排: {exc}")
    return _model


def _lexical_overlap(query: str, text: str) -> float:
    q = set(query.lower().split())
    d = set(text.lower().split())
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)


class Reranker:
    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = model

    def rerank(self, query: str, documents: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        if not documents:
            return []
        model = _load_model(self.model)
        if model is not None:
            try:
                pairs = [(query, str(d.get("text", ""))) for d in documents]
                scores = model.predict(pairs)
                for doc, score in zip(documents, scores):
                    doc["rerank_score"] = float(score)
                ranked = sorted(documents, key=lambda d: d.get("rerank_score", 0.0), reverse=True)
                return ranked[:top_k]
            except Exception as exc:
                logger.warning(f"[Reranker] 预测失败，降级启发式: {exc}")
        # 降级：原始分数 0.6 + 词法重合 0.4 混合排序（优于直接截断）
        for doc in documents:
            base = float(doc.get("score", 0.0))
            lex = _lexical_overlap(query, str(doc.get("text", "")))
            doc["rerank_score"] = 0.6 * base + 0.4 * lex
        ranked = sorted(documents, key=lambda d: d.get("rerank_score", 0.0), reverse=True)
        return ranked[:top_k]


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
