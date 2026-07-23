"""app/config/rag.py — RAG 知识库配置"""

from dataclasses import dataclass


@dataclass
class RAGConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    vector_store: str = "faiss"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    bm25_weight: float = 0.3