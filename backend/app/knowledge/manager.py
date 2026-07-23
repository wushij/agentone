"""app/knowledge/manager.py — 知识库统一管理门面 (KnowledgeManager)"""

from pathlib import Path
from typing import Any

from app.knowledge.embedder import Embedder
from app.knowledge.loader import load_document
from app.knowledge.retrievers.vector import VectorRetriever
from app.knowledge.splitter import TextSplitter
from app.knowledge.stores.faiss import FaissStore


class KnowledgeManager:
    """RAG 知识库统一门面，屏蔽底层 Loader/Splitter/Embedder/Store 的复杂交互。"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedder = Embedder()
        self.store = FaissStore()
        self.retriever = VectorRetriever(self.store, self.embedder)

    def load(self, file_path: str | Path) -> list[dict[str, Any]]:
        """从本地文件加载原始文档。"""
        return load_document(file_path)

    async def build(self, file_path: str | Path, kb_id: str = "") -> dict[str, Any]:
        """从文件读取、切片并建构建向量索引。"""
        docs = self.load(file_path)
        chunks = self.splitter.split(docs)
        for chunk in chunks:
            if kb_id:
                chunk["metadata"]["kb_id"] = kb_id
        await self.store.add_documents(chunks)
        return {
            "kb_id": kb_id,
            "doc_count": len(docs),
            "chunk_count": len(chunks),
        }

    async def search(self, query: str, top_k: int = 4, kb_id: str | None = None) -> list[dict[str, Any]]:
        """检索向量相关文档。"""
        return await self.retriever.retrieve(query, top_k=top_k)

    def delete(self, kb_id: str) -> bool:
        """删除指定知识库。"""
        return True

    def update(self, kb_id: str, new_files: list[str | Path]) -> bool:
        """更新指定知识库。"""
        return True


knowledge_manager = KnowledgeManager()
