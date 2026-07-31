"""app/knowledge/retrievers/vector.py — 向量检索器（委托 RagService 真实检索）"""

from typing import Any


class VectorRetriever:
    def __init__(self, store: Any = None, embedder: Any = None, top_k: int = 5):
        self.store = store
        self.embedder = embedder
        self.top_k = top_k

    async def retrieve(self, query: str, kb_ids: list[str] | None = None, top_k: int | None = None) -> list[dict[str, Any]]:
        """按知识库检索相关片段；未指定 kb_ids 时检索全部知识库。"""
        from app.services.rag.rag_service import RagService

        ids = list(kb_ids or [])
        if not ids:
            try:
                from app.services.rag.kb_store import load_all

                ids = [str(kb.get("id")) for kb in load_all() if kb.get("id")]
            except Exception:
                return []
        if not ids:
            return []
        chunks = await RagService.fetch_kb_chunks_multi(ids, query)
        return chunks[: top_k or self.top_k]

    async def add_documents(self, documents: list[dict[str, Any]], kb_id: str) -> None:
        # 入库走 RagService.index_file_in_kb（文件级），此处不再提供旁路写入
        raise NotImplementedError("请使用 RagService.index_file_in_kb 入库")
